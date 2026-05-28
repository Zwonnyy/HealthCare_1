from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.guides import GuideResponse
from app.models.users import User
from app.services.guides import GuideService

guide_router = APIRouter(prefix="/guides", tags=["guides"])


@guide_router.get("/{guide_id}", response_model=GuideResponse, status_code=status.HTTP_200_OK)
async def get_guide(
    guide_id: int,
    user: Annotated[User, Depends(get_request_user)],
    guide_service: Annotated[GuideService, Depends(GuideService)],
) -> Response:
    guide = await guide_service.get_guide(user=user, guide_id=guide_id)
    return Response(GuideResponse.model_validate(guide).model_dump(), status_code=status.HTTP_200_OK)