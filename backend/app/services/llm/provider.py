import asyncio
import logging
import time
from typing import Protocol, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger("placement_copilot.llm")

T = TypeVar("T", bound=BaseModel)

class LLMProvider(Protocol):
    async def generate_json(self, prompt: str, schema: type[T], system_instruction: str | None = None) -> T:
        ...

    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

class GeminiProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
        fallback_model: str | None = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.fallback_model = fallback_model if fallback_model is not None else settings.GEMINI_FALLBACK_MODEL
        self.embedding_model = embedding_model or settings.GEMINI_EMBEDDING_MODEL
        # Primary first, then the fallback (if set and different). Order preserved, duplicates removed.
        self.models = [m for m in dict.fromkeys([self.model, self.fallback_model]) if m]
        self.total_timeout = float(settings.LLM_TIMEOUT_SECONDS)
        self.attempt_timeout = float(settings.LLM_ATTEMPT_TIMEOUT_SECONDS)
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def _build_config(self, schema: type[T], system_instruction: str | None) -> types.GenerateContentConfig:
        kwargs = dict(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.2,
            system_instruction=system_instruction,
        )
        # Thinking off by default: much faster for short, schema-bound JSON. -1 keeps the model default.
        if settings.LLM_THINKING_BUDGET >= 0:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=settings.LLM_THINKING_BUDGET)
        return types.GenerateContentConfig(**kwargs)

    async def _call(self, model: str, contents: str, config: types.GenerateContentConfig, timeout: float) -> str:
        # Async client + hard timeout so a slow or overloaded API never blocks the server.
        response = await asyncio.wait_for(
            self.client.aio.models.generate_content(model=model, contents=contents, config=config),
            timeout=timeout,
        )
        return response.text

    async def generate_json(self, prompt: str, schema: type[T], system_instruction: str | None = None) -> T:
        if not self.client:
            raise RuntimeError("Gemini API key is not configured")

        config = self._build_config(schema, system_instruction)
        deadline = time.monotonic() + self.total_timeout
        last_error: Exception | None = None

        for model in self.models:
            # Two attempts per model, but the second only happens after invalid JSON.
            for attempt in range(2):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise last_error or asyncio.TimeoutError("LLM time budget exhausted")
                contents = prompt if attempt == 0 else prompt + "\n\nCRITICAL: Respond STRICTLY with schema-valid JSON."
                try:
                    raw_text = await self._call(model, contents, config, min(self.attempt_timeout, remaining))
                    return schema.model_validate_json(raw_text)
                except ValidationError as e:
                    last_error = e
                    logger.warning(f"Gemini {model} returned invalid JSON (attempt {attempt + 1}); retrying once on same model.")
                    continue
                except Exception as e:
                    # Timeout, 503, 400, quota, etc.: move on to the next model, never wait again on this one.
                    last_error = e
                    logger.warning(f"Gemini {model} failed with {type(e).__name__}: {str(e)[:120]}")
                    break

        raise last_error or RuntimeError("All Gemini models failed")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            raise RuntimeError("Gemini API key is not configured")

        if not texts:
            return []

        # Batch embed contents (async client + hard timeout)
        response = await asyncio.wait_for(
            self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=texts,
            ),
            timeout=self.attempt_timeout,
        )
        # response.embeddings is a list of ContentEmbedding objects
        embeddings = [list(e.values) for e in response.embeddings]
        return embeddings


class FakeProvider:
    """Deterministic LLM Provider for unit testing and CI."""
    def __init__(self):
        self.call_count = 0

    async def generate_json(self, prompt: str, schema: type[T], system_instruction: str | None = None) -> T:
        self.call_count += 1

        # Inspect target schema to return realistic deterministic mocks
        schema_name = schema.__name__

        if "ATSSuggestionsResponse" in schema_name:
            mock_data = {
                "suggestions": [
                    {
                        "target_bullet": "Worked on backend microservices with python and database.",
                        "issue": "Lacks measurable impact metrics and weak action verb.",
                        "rewrite": "Architected high-throughput backend microservices using Python and PostgreSQL, improving query latency by [metric]% and scaling to [metric] daily active users.",
                    },
                    {
                        "target_bullet": "Assisted with frontend web page designs.",
                        "issue": "Passive phrasing and missing specific technologies.",
                        "rewrite": "Engineered responsive, accessible React and Tailwind CSS interfaces, reducing first contentful paint by [metric]ms across mobile devices.",
                    }
                ]
            }
            return schema.model_validate(mock_data)

        if "InterviewEvaluation" in schema_name:
            mock_data = {
                "scores": {
                    "correctness": 8.5,
                    "depth": 8.0,
                    "structure": 8.5,
                    "communication": 9.0,
                    "complexity_analysis": 8.0,
                    "edge_cases": 7.5,
                },
                "overall": 8.35,
                "strengths": [
                    "Clearly articulated time and space complexity trade-offs upfront.",
                    "Correctly handled off-by-one pointer convergence bounds.",
                ],
                "gaps": [
                    "Could explicitly mention memory layout and cache locality benefits.",
                ],
                "improved_answer": "To optimize the solution further, establish the invariant mid = left + (right - left) // 2 to avoid overflow, maintaining O(1) auxiliary space.",
                "follow_up_question": "How would you modify this approach if the input array had millions of duplicates or was distributed across network shards?",
            }
            return schema.model_validate(mock_data)

        if "GeneratedQuestion" in schema_name:
            mock_data = {
                "topic": "Distributed Caching",
                "difficulty": 3.0,
                "text": "How would you design a distributed caching layer that avoids cache stampedes when a popular key expires?",
                "ideal_points": [
                    "Mutex locks or single-flight request coalescing",
                    "Probabilistic early expiration (XFetch)",
                    "Background asynchronous cache warming",
                ],
            }
            return schema.model_validate(mock_data)

        # Fallback empty construction
        return schema.model_validate({})

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Return deterministic mock embeddings of dimension 8
        embeddings = []
        for text in texts:
            val = float(len(text) % 10) / 10.0
            embeddings.append([val, 1.0 - val, 0.5, 0.25, 0.75, val * 0.5, 0.1, 0.9])
        return embeddings

# Global provider instance
_provider: LLMProvider | None = None

def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        provider_name = settings.LLM_PROVIDER.lower()
        if settings.APP_ENV == "production" and provider_name == "fake":
            raise RuntimeError("LLM_PROVIDER cannot be configured to 'fake' in production environment")

        if provider_name == "fake":
            _provider = FakeProvider()
        elif settings.GEMINI_API_KEY and settings.APP_ENV != "test":
            _provider = GeminiProvider()
        else:
            _provider = FakeProvider()
    return _provider

def set_llm_provider(provider: LLMProvider) -> None:
    global _provider
    _provider = provider
