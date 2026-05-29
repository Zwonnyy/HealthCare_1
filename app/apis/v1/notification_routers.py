from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.notifications import NotificationResponse, UnreadCountResponse
from app.dtos.pagination import PaginatedResponse, PaginationParams
from app.models.users import User
from app.services.notifications import NotificationService

notification_router = APIRouter(prefix="/notifications", tags=["notifications"])


@notification_router.get("", response_model=PaginatedResponse[NotificationResponse], status_code=status.HTTP_200_OK)
async def get_notifications(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
    pagination: Annotated[PaginationParams, Depends()],
) -> Response:
    notifications, total = await service.get_notifications(user=user, offset=pagination.offset, limit=pagination.size)
    return Response(
        PaginatedResponse.create(
            items=[NotificationResponse.model_validate(n) for n in notifications],
            total=total,
            page=pagination.page,
            size=pagination.size,
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@notification_router.get("/unread-count", response_model=UnreadCountResponse, status_code=status.HTTP_200_OK)
async def get_unread_count(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> Response:
    count = await service.get_unread_count(user=user)
    return Response(UnreadCountResponse(count=count).model_dump(), status_code=status.HTTP_200_OK)


@notification_router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    notification_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> None:
    await service.mark_as_read(user=user, notification_id=notification_id)


@notification_router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_as_read(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[NotificationService, Depends(NotificationService)],
) -> None:
    await service.mark_all_as_read(user=user)
