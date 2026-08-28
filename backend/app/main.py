from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

BUILD_ID = "2026-08-28-ssl-drip-v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        import app.models  # noqa: F401
        from app.core.database import init_db

        await init_db()
    except Exception as e:
        print(f"WARNING: startup DB/models error: {e}")
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} build {BUILD_ID} started")
    yield
    print("Shutting down...")


app = FastAPI(
    title="TiltShield",
    version=settings.APP_VERSION,
    description="Behavioral risk management for traders and prop desks.",
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
    return {"status": "ok", "build": BUILD_ID, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "app": "TiltShield",
        "version": settings.APP_VERSION,
        "build": BUILD_ID,
        "status": "running",
        "message": "Know when trading is breaking down before the account does.",
    }


try:
    from app.api import api_router

    app.include_router(api_router, prefix="/api/v1")
    print(f"API router loaded · build {BUILD_ID}")
except Exception as e:
    print(f"WARNING: API routers failed to load: {e}")
