import asyncio
import os
import sys
from dotenv import load_dotenv

# Load backend/.env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from google import genai

async def check_db(name: str, url: str):
    print(f"Checking {name} connection...")
    if not url:
        raise ValueError(f"Missing {name} URL in environment")
    
    # Neon pgbouncer requires prepare_threshold=None
    engine = create_async_engine(
        url,
        connect_args={"prepare_threshold": None},
        pool_pre_ping=True,
    )
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1;"))
            val = result.scalar()
            if val == 1:
                print(f"✓ {name} connected successfully (SELECT 1 -> {val})")
            else:
                raise ValueError(f"{name} unexpected result: {val}")
    finally:
        await engine.dispose()

def check_gemini():
    print("Checking Gemini API key and model availability...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment")
    
    client = genai.Client(api_key=api_key)
    # List models to verify connectivity and credentials
    models = list(client.models.list(config={"page_size": 10}))
    model_names = [m.name for m in models]
    print(f"✓ Gemini API connected. Available models sample: {model_names[:3]}")

async def main():
    print("=== Phase 1 Preflight Verification ===")
    pooled_url = os.getenv("DATABASE_URL")
    direct_url = os.getenv("DATABASE_URL_DIRECT")
    
    await check_db("DATABASE_URL (Pooled)", pooled_url)
    await check_db("DATABASE_URL_DIRECT (Direct)", direct_url)
    check_gemini()
    print("=== All Phase 1 Preflight Gates Passed! ===")

if __name__ == "__main__":
    asyncio.run(main())
