from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Supabase / Postgres need SSL. SQLite does not.
_connect_args = {}
_url = settings.DATABASE_URL or ""
if _url.startswith("postgresql") or _url.startswith("postgres"):
    _connect_args = {"ssl": "require"}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args=_connect_args,
    pool_pre_ping=True,
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
    """Create tables. Do not crash the whole app if DB is temporarily unreachable."""
    from pathlib import Path

    db_url = settings.DATABASE_URL or ""
    if "sqlite" in db_url and ":///" in db_url:
        path = db_url.split(":///./")[-1] if ":///./" in db_url else None
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables ready")
    except Exception as e:
        # App still starts so /health works; fix DATABASE_URL and redeploy
        print(f"WARNING: init_db failed (check DATABASE_URL): {e}")
