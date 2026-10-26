from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db

router = APIRouter(tags=["ops"])

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "Placement Copilot",
        "version": "0.1.0",
    }

@router.get("/health/db")
async def health_db_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1;"))
    val = result.scalar()
    return {
        "status": "ok" if val == 1 else "unhealthy",
        "db": "connected" if val == 1 else "error",
    }
