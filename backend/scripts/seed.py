import asyncio
import json
import os
import sys

from dotenv import load_dotenv

# Add backend to sys.path and load .env
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.models import (
    DSAProblem,
    DSATopic,
    InterviewTrack,
    ProblemTopic,
    QuestionBank,
)

DATA_DIR = os.path.join(BASE_DIR, "app", "data")

async def seed_dsa_topics(db: AsyncSession):
    with open(os.path.join(DATA_DIR, "dsa_topics.json"), encoding="utf-8") as f:
        topics_data = json.load(f)

    print(f"Seeding {len(topics_data)} DSA topics...")
    existing_topics = {t.slug: t for t in (await db.execute(select(DSATopic))).scalars().all()}
    topic_map = {}

    for item in topics_data:
        slug = item["slug"]
        if slug in existing_topics:
            existing = existing_topics[slug]
            existing.name = item["name"]
            existing.category = item["category"]
            existing.importance = item["importance"]
            existing.target_points = item.get("target_points", 12.0)
            topic_map[slug] = existing
        else:
            new_topic = DSATopic(
                slug=slug,
                name=item["name"],
                category=item["category"],
                importance=item["importance"],
                target_points=item.get("target_points", 12.0),
            )
            db.add(new_topic)
            topic_map[slug] = new_topic

    await db.flush()
    # Reload topic_map with IDs if new ones added
    all_topics = (await db.execute(select(DSATopic))).scalars().all()
    topic_map = {t.slug: t for t in all_topics}
    await db.commit()
    print("✓ DSA topics seeded successfully.")
    return topic_map

async def seed_dsa_problems(db: AsyncSession, topic_map: dict):
    with open(os.path.join(DATA_DIR, "dsa_problems.json"), encoding="utf-8") as f:
        problems_data = json.load(f)

    print(f"Seeding {len(problems_data)} DSA problems in bulk...")
    existing_problems = {p.slug: p for p in (await db.execute(select(DSAProblem))).scalars().all()}
    existing_links = set(
        (link.problem_id, link.topic_id)
        for link in (await db.execute(select(ProblemTopic))).scalars().all()
    )

    for item in problems_data:
        slug = item["slug"]
        if slug in existing_problems:
            problem = existing_problems[slug]
            problem.title = item["title"]
            problem.difficulty = item["difficulty"]
            problem.frequency = item.get("frequency", 0.5)
        else:
            problem = DSAProblem(
                slug=slug,
                title=item["title"],
                difficulty=item["difficulty"],
                platform=item.get("platform", "LeetCode"),
                url=item.get("url"),
                frequency=item.get("frequency", 0.5),
            )
            db.add(problem)
            existing_problems[slug] = problem

    await db.flush()
    # Refresh map with IDs
    all_problems = {p.slug: p for p in (await db.execute(select(DSAProblem))).scalars().all()}

    for item in problems_data:
        problem = all_problems.get(item["slug"])
        if not problem:
            continue
        for topic_slug in item.get("topic_slugs", []):
            if topic_slug in topic_map:
                topic_id = topic_map[topic_slug].id
                link_key = (problem.id, topic_id)
                if link_key not in existing_links:
                    db.add(ProblemTopic(problem_id=problem.id, topic_id=topic_id))
                    existing_links.add(link_key)

    await db.commit()
    print("✓ DSA problems and topic links seeded successfully.")

async def seed_question_bank(db: AsyncSession):
    with open(os.path.join(DATA_DIR, "question_bank.json"), encoding="utf-8") as f:
        questions_data = json.load(f)

    print(f"Seeding {len(questions_data)} interview questions in bulk...")
    all_qb = (await db.execute(select(QuestionBank))).scalars().all()
    existing_qb = {(q.track, q.topic, q.question_text): q for q in all_qb}

    for item in questions_data:
        track_enum = InterviewTrack(item["track"])
        key = (track_enum, item["topic"], item["question_text"])
        if key in existing_qb:
            existing = existing_qb[key]
            existing.difficulty = item["difficulty"]
            existing.ideal_points = item["ideal_points"]
        else:
            qb = QuestionBank(
                track=track_enum,
                topic=item["topic"],
                difficulty=item["difficulty"],
                question_text=item["question_text"],
                ideal_points=item["ideal_points"],
            )
            db.add(qb)
            existing_qb[key] = qb

    await db.commit()
    print("✓ Question bank seeded successfully.")

async def run_seed(db_url: str = None, session: AsyncSession = None):
    if session is not None:
        topic_map = await seed_dsa_topics(session)
        await seed_dsa_problems(session, topic_map)
        await seed_question_bank(session)
        return

    if not db_url:
        db_url = settings.DATABASE_URL
    engine = create_async_engine(db_url, connect_args={"prepare_threshold": None})
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=== Running Bulk Idempotent Seed Script ===")
    async with session_factory() as s:
        topic_map = await seed_dsa_topics(s)
        await seed_dsa_problems(s, topic_map)
        await seed_question_bank(s)
    
    await engine.dispose()
    print("=== Database Seeding Complete! ===")

if __name__ == "__main__":
    asyncio.run(run_seed())
