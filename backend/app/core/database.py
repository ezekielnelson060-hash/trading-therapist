from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

_url = (settings.DATABASE_URL or "").strip()

# asyncpg: use ssl=True for Supabase. SQLite needs no connect_args.
_connect_args = {}
if _url.startswith("postgresql") or _url.startswith("postgres"):
    _connect_args = {"ssl": True}

engine = create_async_engine(
    _url,
    echo=bool(settings.DEBUG),
    future=True,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create tables. Never block / crash the process for long."""
    import asyncio
    from pathlib import Path

    db_url = _url
    if "sqlite" in db_url and ":///" in db_url:
        path = db_url.split(":///./")[-1] if ":///./" in db_url else None
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        await asyncio.wait_for(_create(), timeout=20.0)
        print("Database tables ready")
    except Exception as e:
        print(f"WARNING: init_db failed (check DATABASE_URL): {type(e).__name__}: {e}")
