from fastapi import APIRouter

from app.apis.v1.appointment_routers import appointment_router
from app.apis.v1.auth_routers import auth_router
from app.apis.v1.chat_routers import chat_router
from app.apis.v1.drug_interaction_routers import drug_interaction_router
from app.apis.v1.health_report_routers import health_report_router
from app.apis.v1.guide_routers import guide_router
from app.apis.v1.health_goal_routers import health_goal_router
from app.apis.v1.health_log_routers import health_log_router
from app.apis.v1.medication_check_routers import medication_check_router
from app.apis.v1.message_routers import message_router
from app.apis.v1.notification_routers import notification_router
from app.apis.v1.record_routers import record_router
from app.apis.v1.stats_routers import stats_router
from app.apis.v1.user_routers import user_router

v1_routers = APIRouter(prefix="/api/v1")
v1_routers.include_router(auth_router)
v1_routers.include_router(user_router)
v1_routers.include_router(record_router)
v1_routers.include_router(drug_interaction_router)
v1_routers.include_router(guide_router)
v1_routers.include_router(health_log_router)
v1_routers.include_router(health_goal_router)
v1_routers.include_router(message_router)
v1_routers.include_router(notification_router)
v1_routers.include_router(stats_router)
v1_routers.include_router(appointment_router)
v1_routers.include_router(medication_check_router)
v1_routers.include_router(chat_router)
v1_routers.include_router(health_report_router)
