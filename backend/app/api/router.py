from fastapi import APIRouter

from app.api.routes import auth, contacts, templates, campaigns, ai, analytics


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(contacts.router)
api_router.include_router(templates.router)
api_router.include_router(campaigns.router)
api_router.include_router(ai.router)
api_router.include_router(analytics.router)
