from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import inside lifespan so a DB/config error does not prevent process start
    try:
        import app.models  # noqa: F401
        from app.core.database import init_db
        await init_db()
    except Exception as e:
        print(f"WARNING: startup DB/models error: {e}")
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started")
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

# Health endpoints first — always available even if routers fail to load
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "Automatic trade data first. Traders cannot lie about what they actually did.",
    }


try:
    from app.api import api_router
    app.include_router(api_router, prefix="/api/v1")
except Exception as e:
    print(f"WARNING: API routers failed to load: {e}")
