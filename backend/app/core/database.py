from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

_url = (settings.DATABASE_URL or "").strip()

if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _url.startswith("postgresql://") and "+asyncpg" not in _url:
    _url = _url.replace("postgresql://", "postgresql+asyncpg://", 1)

_connect_args = {}
if "postgresql" in _url:
    _connect_args = {"ssl": True}

print(f"DB engine URL scheme: {_url.split('://')[0] if '://' in _url else 'invalid'}")

engine = create_async_engine(
    _url,
    echo=False,
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
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db():
    import asyncio
    from pathlib import Path

    if "sqlite" in _url and ":///" in _url:
        path = _url.split(":///./")[-1] if ":///./" in _url else None
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        await asyncio.wait_for(_create(), timeout=25.0)
        print("Database tables ready")
        await ensure_schema()
    except Exception as e:
        print(f"WARNING: init_db failed (check DATABASE_URL): {type(e).__name__}: {e}")


async def ensure_schema():
    if "postgresql" not in _url:
        return
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS trading_locked BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS trading_locked_until TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS trading_lock_reason VARCHAR(255)",
    ]
    try:
        async with engine.begin() as conn:
            for sql in statements:
                await conn.exec_driver_sql(sql)
        print("Schema ensure: user lock/billing columns OK")
    except Exception as e:
        print(f"WARNING: ensure_schema: {e}")
