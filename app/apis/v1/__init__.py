from fastapi import APIRouter

from app.apis.v1.auth_routers import auth_router
from app.apis.v1.guide_routers import guide_router
from app.apis.v1.health_log_routers import health_log_router
from app.apis.v1.message_routers import message_router
from app.apis.v1.record_routers import record_router
from app.apis.v1.user_routers import user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(record_router)
v1_routers.include_router(guide_router)
v1_routers.include_router(health_log_router)
v1_routers.include_router(message_router)
