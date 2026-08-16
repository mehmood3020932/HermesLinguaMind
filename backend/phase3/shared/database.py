"""
Hermes LinguaMind — Shared Database Session (Phase 3)
Real async Postgres session factory, reused by any phase3 service that
needs durable persistence instead of an in-process dict.
"""

import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://hermes:hermes@postgres:5432/hermes_db")

engine = create_async_engine(
    DATABASE_URL, pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=1800, echo=False,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def db_healthy() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def init_db() -> None:
    """Create every table declared on shared.models.common.Base if it does not
    already exist yet (CREATE TABLE IF NOT EXISTS semantics — safe to call
    from more than one service's startup, and a no-op on every call after
    the first). This is what actually turns the ORM models in
    shared/models/common.py into real Postgres tables; without calling this
    once, every query against them fails with 'relation "users" does not
    exist' (and equivalents for coin_balances, memories, etc).

    For a larger team this would be Alembic-managed migrations instead of
    create_all(); create_all() is the pragmatic choice for a single-image,
    self-hosted deployment with no separate migration step in CI.

    Serialized with a Postgres advisory lock: api_gateway, coin_ledger, and
    memory all call this on their own startup, and supervisord starts all
    of them at roughly the same moment on container boot. Verified this
    matters — running them concurrently against a fresh database, 2 of 3
    calls fail with `UniqueViolationError: duplicate key ... pg_type_typname`
    (Postgres ENUM types don't have IF-NOT-EXISTS semantics, and
    create_all()'s own check-then-create isn't atomic across sessions).
    supervisord's autorestart would eventually paper over that with a
    restart, but that means every fresh deployment guarantees 2 failed
    service starts. pg_advisory_xact_lock makes concurrent callers queue
    up instead of racing, and auto-releases when the transaction ends
    (including on error), so a crash mid-init can't leave it stuck locked.
    """
    from shared.models.common import Base  # local import: avoids a circular import at module load time

    _INIT_DB_LOCK_KEY = 872134599  # arbitrary fixed key, unique to this lock's purpose

    async with engine.begin() as conn:
        await conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _INIT_DB_LOCK_KEY})
        await conn.run_sync(Base.metadata.create_all)
