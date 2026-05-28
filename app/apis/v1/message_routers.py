from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.messages import MessageResponse, MessageSendRequest
from app.models.users import User
from app.services.messages import MessageService

message_router = APIRouter(prefix="/messages", tags=["messages"])


@message_router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    request: MessageSendRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MessageService, Depends(MessageService)],
) -> Response:
    message = await service.send_message(sender=user, data=request)
    return Response(MessageResponse.model_validate(message).model_dump(), status_code=status.HTTP_201_CREATED)


@message_router.get("/inbox", response_model=list[MessageResponse], status_code=status.HTTP_200_OK)
async def get_inbox(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MessageService, Depends(MessageService)],
) -> Response:
    messages = await service.get_inbox(user=user)
    return Response([MessageResponse.model_validate(m).model_dump() for m in messages], status_code=status.HTTP_200_OK)


@message_router.get("/sent", response_model=list[MessageResponse], status_code=status.HTTP_200_OK)
async def get_sent(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MessageService, Depends(MessageService)],
) -> Response:
    messages = await service.get_sent(user=user)
    return Response([MessageResponse.model_validate(m).model_dump() for m in messages], status_code=status.HTTP_200_OK)


@message_router.get("/unread-count", status_code=status.HTTP_200_OK)
async def get_unread_count(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MessageService, Depends(MessageService)],
) -> Response:
    count = await service.get_unread_count(user=user)
    return Response({"unread_count": count}, status_code=status.HTTP_200_OK)


@message_router.get("/{message_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def get_message(
    message_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[MessageService, Depends(MessageService)],
) -> Response:
    message = await service.get_message(user=user, message_id=message_id)
    return Response(MessageResponse.model_validate(message).model_dump(), status_code=status.HTTP_200_OK)
