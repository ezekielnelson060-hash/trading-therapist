from fastapi import APIRouter
from app.api import (
    onboarding,
    trades,
    brokers,
    analytics,
    chat,
    auth,
    connectors,
    plans,
    checkins,
    alerts,
    lock,
    billing,
    teams,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(brokers.router, prefix="/brokers", tags=["brokers"])
api_router.include_router(trades.router, prefix="/trades", tags=["trades"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(connectors.router, prefix="/connectors", tags=["connectors"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(checkins.router, prefix="/checkins", tags=["checkins"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(lock.router, prefix="/lock", tags=["lock"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
