from fastapi import APIRouter
from app.api import trades, brokers, analytics, chat, auth, connectors, plans

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(brokers.router, prefix="/brokers", tags=["brokers"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(connectors.router, prefix="/connectors", tags=["connectors"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
