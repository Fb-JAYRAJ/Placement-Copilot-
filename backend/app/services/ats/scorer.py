import json
import re
from typing import Any

import numpy as np
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.ats.extractor import get_taxonomy_matcher
from app.services.llm.provider import get_llm_provider

ACTION_VERBS = {
    "accelerated", "accomplished", "achieved", "acquired", "acted", "activated", "adapted",
    "administered", "advanced", "advised", "allocated", "analyzed", "applied", "appraised",
    "arbitrated", "architected", "arranged", "assembled", "assessed", "assigned", "assisted",
    "audited", "augmented", "authored", "automated", "balanced", "benchmarked", "blockaded",
    "boosted", "briefed", "budgeted", "built", "calculated", "calibrated", "capitalized",
    "captured", "cataloged", "championed", "charted", "clarified", "classified", "coached",
    "collaborated", "collected", "commissioned", "communicated", "compiled", "composed",
    "computed", "conceptualized", "condensed", "conducted", "configured", "consolidated",
    "constructed", "consulted", "contacted", "continued", "contracted", "controlled",
    "converted", "conveyed", "coordinated", "corrected", "counseled", "crafted", "created",
    "critiqued", "cultivated", "customized", "debugged", "decided", "defined", "delegated",
    "delivered", "demonstrated", "deployed", "designed", "detailed", "detected", "determined",
    "developed", "devised", "diagnosed", "directed", "discovered", "dispatched", "drafted",
    "drove", "earned", "edited", "educated", "effected", "elicited", "empowered", "enabled",
    "enacted", "encouraged", "engineered", "enhanced", "enlarged", "enlisted", "ensured",
    "entered", "established", "estimated", "evaluated", "examined", "executed", "expanded",
    "expedited", "experimented", "explained", "explored", "extended", "extracted", "fabricated",
    "facilitated", "fashioned", "fielded", "figured", "finalized", "financed", "focused",
    "forecasted", "formed", "formulated", "fostered", "founded", "fulfilled", "functioned",
    "gained", "gathered", "generated", "governed", "graduated", "guided", "handled",
    "headed", "heightened", "hired", "hosted", "identified", "illustrated", "implemented",
    "improved", "improvised", "increased", "indexed", "individualized", "influenced",
    "informed", "initiated", "innovated", "inspected", "inspired", "installed", "instituted",
    "instructed", "integrated", "intended", "intensified", "interacted", "interpreted",
    "interviewed", "introduced", "invented", "investigated", "isolated", "issued", "joined",
    "judged", "justified", "launched", "lead", "led", "lectured", "lessened", "licensed",
    "lightened", "linked", "lobbied", "localized", "located", "logged", "made", "maintained",
    "managed", "manipulated", "manufactured", "mapped", "marketed", "maximized", "measured",
    "mediated", "mentored", "merged", "migrated", "minimized", "modeled", "moderated",
    "modernized", "modified", "monitored", "motivated", "navigated", "negotiated", "networked",
    "neutralized", "nominated", "normalized", "nurtured", "observed", "obtained", "occupied",
    "operated", "optimized", "orchestrated", "ordered", "organized", "originated", "outlined",
    "overcame", "overhauled", "oversaw", "packaged", "partnered", "performed", "persuaded",
    "piloted", "pioneered", "placed", "planned", "pointed", "policed", "policied", "polished",
    "positioned", "predicted", "prepared", "prescribed", "presented", "preserved", "presided",
    "prevented", "priced", "printed", "prioritized", "probed", "processed", "procured",
    "produced", "profiled", "programmed", "projected", "promoted", "prompted", "proposed",
    "proved", "provided", "publicized", "published", "purchased", "pursued", "qualified",
    "quantified", "questioned", "raised", "ranked", "rated", "reached", "realized", "reasoned",
    "received", "recognized", "recommended", "reconciled", "recorded", "recruited", "redesigned",
    "reduced", "reevaluated", "referred", "refined", "refocused", "refactored", "regulated",
    "reinforced", "reorganized", "repaired", "replaced", "replenished", "reported", "represented",
    "researched", "reshaped", "resolved", "responded", "restored", "restructured", "retained",
    "retrieved", "revamped", "reviewed", "revised", "revitalized", "rewarded", "routed",
    "saved", "scaled", "scheduled", "screened", "scrutinized", "secured", "selected",
    "separated", "served", "serviced", "settled", "shaped", "shared", "shifted", "shipped",
    "shortened", "simplified", "simulated", "slashed", "solicited", "solved", "spearheaded",
    "specialized", "specified", "standardized", "started", "stimulated", "strategized",
    "streamlined", "strengthened", "structured", "substantiated", "succeeded", "summarized",
    "supervised", "supplemented", "supplied", "supported", "surpassed", "surveyed", "synthesized",
    "systematized", "tabulated", "tailored", "targeted", "taught", "terminated", "tested",
    "tracked", "trained", "transcribed", "transformed", "translated", "transmitted", "transported",
    "troubleshot", "unified", "unraveled", "updated", "upgraded", "utilized", "validated",
    "valued", "verified", "visualized", "won", "wrote"
}

class ATSSuggestionItem(BaseModel):
    target_bullet: str
    issue: str
    rewrite: str

class ATSSuggestionsResponse(BaseModel):
    suggestions: list[ATSSuggestionItem]

def compute_quality_score(parsed_resume: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """
    quality = 30% standard sections and contact info,
              25% bullets starting with an action verb,
              25% bullets containing a number,
              20% length in the 350–900-word range.
    """
    sections = parsed_resume.get("sections", {})
    contact = parsed_resume.get("contact_info", {})
    bullets = parsed_resume.get("bullets", [])
    word_count = parsed_resume.get("word_count", 0)

    # 1. Standard sections and contact info (30 pts max)
    core_sections = ["education", "experience", "projects", "skills"]
    found_sections = [s for s in core_sections if s in sections and len(sections[s]) > 20]
    section_score = (len(found_sections) / len(core_sections)) * 20.0
    contact_score = 10.0 if contact.get("has_contact") else 0.0
    sec_contact_total = section_score + contact_score  # 0 to 30

    # 2. Bullets starting with an action verb (25 pts max)
    action_verb_bullets = 0
    numeric_bullets = 0
    total_bullets = len(bullets)

    metric_pattern = re.compile(r"(\b\d+[\.,]?\d*\b|\$|\%|\bx\b)", re.IGNORECASE)

    for bullet in bullets:
        words = re.findall(r"\b[a-zA-Z]+\b", bullet.lower())
        if words and words[0] in ACTION_VERBS:
            action_verb_bullets += 1
        if metric_pattern.search(bullet):
            numeric_bullets += 1

    if total_bullets > 0:
        action_verb_score = (action_verb_bullets / total_bullets) * 25.0
        numeric_score = (numeric_bullets / total_bullets) * 25.0
    else:
        action_verb_score = 10.0
        numeric_score = 10.0

    # 3. Length in the 350-900 word range (20 pts max)
    if 350 <= word_count <= 900:
        length_score = 20.0
    elif 200 <= word_count < 350:
        length_score = 20.0 * (word_count - 100) / 250.0
    elif 900 < word_count <= 1300:
        length_score = max(5.0, 20.0 * (1.0 - (word_count - 900) / 400.0))
    else:
        length_score = max(0.0, 5.0)

    total_quality = min(100.0, max(0.0, sec_contact_total + action_verb_score + numeric_score + length_score))

    findings = {
        "word_count": word_count,
        "standard_sections_detected": found_sections,
        "has_contact_info": contact.get("has_contact", False),
        "total_bullets_analyzed": total_bullets,
        "action_verb_bullets": action_verb_bullets,
        "metric_bullets": numeric_bullets,
        "section_score": round(sec_contact_total, 1),
        "action_verb_score": round(action_verb_score, 1),
        "numeric_score": round(numeric_score, 1),
        "length_score": round(length_score, 1),
    }

    return round(total_quality, 2), findings

def compute_tfidf_score(resume_text: str, jd_text: str) -> float:
    """
    tfidf = cosine of TF-IDF vectors (1–2-grams, sublinear tf, English stop words)
    as min(100, 100·cos/0.45).
    """
    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
        )
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        cos_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        # min(100, 100 * cos / 0.45)
        scaled_score = min(100.0, max(0.0, (cos_sim / 0.45) * 100.0))
        return round(float(scaled_score), 2)
    except Exception:
        return 50.0

async def compute_semantic_score(resume_chunks: list[str], jd_sentences: list[str]) -> tuple[float | None, bool]:
    """
    semantic = embed JD requirement sentences and resume chunks,
    take each requirement's max cosine over chunks, average,
    then 100·clip((avg−0.45)/0.40, 0, 1).
    Returns (score, degraded)
    """
    if not resume_chunks or not jd_sentences:
        return None, True

    provider = get_llm_provider()
    try:
        # Embed JD sentences and resume chunks
        all_texts = jd_sentences + resume_chunks
        embeddings = await provider.embed(all_texts)
        if not embeddings or len(embeddings) != len(all_texts):
            return None, True

        jd_embs = np.array(embeddings[:len(jd_sentences)])
        resume_embs = np.array(embeddings[len(jd_sentences):])

        # Normalize rows to unit vectors
        jd_norms = np.linalg.norm(jd_embs, axis=1, keepdims=True)
        resume_norms = np.linalg.norm(resume_embs, axis=1, keepdims=True)
        
        jd_norms[jd_norms == 0] = 1e-9
        resume_norms[resume_norms == 0] = 1e-9

        jd_unit = jd_embs / jd_norms
        resume_unit = resume_embs / resume_norms

        # Cosine similarity matrix: (num_jd, num_resume)
        sim_matrix = np.dot(jd_unit, resume_unit.T)
        
        # Max cosine for each JD sentence over all resume chunks
        max_cosines = np.max(sim_matrix, axis=1)
        avg_cos = float(np.mean(max_cosines))

        # 100 * clip((avg - 0.45) / 0.40, 0, 1)
        scaled = 100.0 * np.clip((avg_cos - 0.45) / 0.40, 0.0, 1.0)
        return round(float(scaled), 2), False
    except Exception:
        # Graceful degradation on embedding failure
        return None, True

async def generate_bullet_suggestions(
    bullets: list[str],
    missing_skills: list[dict[str, Any]],
    jd_role: str,
) -> list[dict[str, Any]]:
    """
    Generates up to 5 grounded bullet rewrite suggestions.
    The LLM may reword but must never invent experience (use placeholders like [metric]).
    """
    if not bullets:
        return []

    provider = get_llm_provider()
    candidate_bullets = bullets[:6]
    missing_names = [s["name"] for s in missing_skills[:4]]

    prompt = f"""You are an expert technical resume coach evaluating alignment for a '{jd_role}' position.
Review these resume bullets:
{json.dumps(candidate_bullets, indent=2)}

High-value missing skills from the job description: {", ".join(missing_names) if missing_names else "None"}

Provide up to 5 actionable suggestions to strengthen these bullets.
Rules:
1. Every suggestion must be grounded in an actual target bullet from the list.
2. Reword using stronger action verbs and quantifiable impact.
3. NEVER invent experience or numbers. Use placeholders such as '[metric]' or '[X%]' where candidate can supply data.
4. If appropriate, demonstrate where missing technical skills can naturally fit.
"""

    system_instruction = "You are a schema-enforced ATS optimization coach. Ground all suggestions in real user input. Never hallucinate experience."

    try:
        result = await provider.generate_json(
            prompt=prompt,
            schema=ATSSuggestionsResponse,
            system_instruction=system_instruction,
        )
        return [item.model_dump() for item in result.suggestions[:5]]
    except Exception:
        # Fallback heuristic suggestions
        fallback = []
        for bullet in candidate_bullets[:3]:
            words = bullet.split()
            first_word = words[0] if words else ""
            if first_word.lower() not in ACTION_VERBS:
                fallback.append({
                    "target_bullet": bullet,
                    "issue": f"Starts with '{first_word}', which is not a recognized strong technical action verb.",
                    "rewrite": f"Engineered and deployed {bullet.lower().rstrip('.')} with [metric]% performance gain.",
                })
            elif not re.search(r"(\d+|\$|\%)", bullet):
                fallback.append({
                    "target_bullet": bullet,
                    "issue": "Lacks measurable quantification or business impact metric.",
                    "rewrite": f"{bullet.rstrip('.')} resulting in [metric]% latency reduction across [metric] active users.",
                })
        return fallback[:5]

async def score_resume_against_jd(
    resume_text: str,
    parsed_resume: dict[str, Any],
    jd_text: str,
    jd_role: str = "Software Engineer",
) -> dict[str, Any]:
    matcher = get_taxonomy_matcher()

    # 1. Extract skills from Resume and JD
    resume_skills = matcher.extract_skills_from_text(resume_text)
    jd_skills = matcher.extract_weighted_skills_from_jd(jd_text)

    resume_skill_ids = {s["skill_id"]: s for s in resume_skills}
    matched_skills = []
    missing_skills = []

    sum_w_matched = 0.0
    sum_w_all_jd = 0.0

    for jd_skill in jd_skills:
        w = jd_skill["weight"]
        sum_w_all_jd += w
        if jd_skill["skill_id"] in resume_skill_ids:
            r_skill = resume_skill_ids[jd_skill["skill_id"]]
            sum_w_matched += w
            matched_skills.append({
                "skill_id": jd_skill["skill_id"],
                "name": jd_skill["name"],
                "category": jd_skill["category"],
                "weight": w,
                "evidence": r_skill.get("evidence", "Mentioned in resume"),
            })
        else:
            missing_skills.append({
                "skill_id": jd_skill["skill_id"],
                "name": jd_skill["name"],
                "category": jd_skill["category"],
                "weight": w,
            })

    # Sub-score: keyword = 100 * Σw(matched)/Σw(all JD skills)
    if sum_w_all_jd > 0:
        keyword_score = round(min(100.0, (sum_w_matched / sum_w_all_jd) * 100.0), 2)
    else:
        keyword_score = 100.0

    # Sub-score: tfidf
    tfidf_score = compute_tfidf_score(resume_text, jd_text)

    # Sub-score: quality
    quality_score, quality_findings = compute_quality_score(parsed_resume)

    # Sub-score: semantic
    jd_sentences = [s.strip() for s in re.split(r"[\.\n]+", jd_text) if len(s.strip()) > 20][:15]
    bullets = parsed_resume.get("bullets", [])
    resume_chunks = bullets if bullets else [p.strip() for p in resume_text.splitlines() if len(p.strip()) > 30][:20]

    semantic_score, degraded = await compute_semantic_score(resume_chunks, jd_sentences)

    # Overall score formula:
    # 0.40·keyword + 0.25·semantic + 0.15·tfidf + 0.20·quality
    if not degraded and semantic_score is not None:
        overall = (
            0.40 * keyword_score
            + 0.25 * semantic_score
            + 0.15 * tfidf_score
            + 0.20 * quality_score
        )
    else:
        # Renormalise when semantic is dropped:
        # keyword: 0.40/0.75 = 0.5333, tfidf: 0.15/0.75 = 0.20, quality: 0.20/0.75 = 0.2667
        degraded = True
        overall = (
            (0.40 / 0.75) * keyword_score
            + (0.15 / 0.75) * tfidf_score
            + (0.20 / 0.75) * quality_score
        )

    overall = round(max(0.0, min(100.0, overall)), 2)

    # Suggestions from LLM
    suggestions = await generate_bullet_suggestions(bullets, missing_skills, jd_role)

    return {
        "overall": overall,
        "keyword_score": keyword_score,
        "semantic_score": semantic_score,
        "tfidf_score": tfidf_score,
        "quality_score": quality_score,
        "matched": matched_skills,
        "missing": missing_skills,
        "suggestions": suggestions,
        "quality_findings": quality_findings,
        "degraded": degraded,
    }
