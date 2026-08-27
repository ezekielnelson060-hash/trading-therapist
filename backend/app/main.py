from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

BUILD_ID = "2026-08-27-ssl-fix"


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        import app.models  # noqa: F401
        from app.core.database import init_db
        await init_db()
    except Exception as e:
        print(f"WARNING: startup DB/models error: {e}")
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started build={BUILD_ID}")
    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Trading Therapist + Behavioral Analytics. Automatic trade data first.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "build": BUILD_ID}


@app.get("/db-check")
async def db_check_root():
    """Root-level DB diagnostic (easy to open in browser)."""
    try:
        from sqlalchemy import text
        from app.core.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"db": "ok", "build": BUILD_ID, "message": "Connected to database"}
    except Exception as e:
        return {
            "db": "error",
            "build": BUILD_ID,
            "type": type(e).__name__,
            "message": str(e),
        }


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "build": BUILD_ID,
        "status": "running",
        "message": "Automatic trade data first. Traders cannot lie about what they actually did.",
    }


try:
    from app.api import api_router

    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    print(f"WARNING: API routers failed to load: {e}")
