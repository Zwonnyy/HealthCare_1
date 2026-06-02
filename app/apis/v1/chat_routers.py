from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies.security import get_request_user
from app.models.users import User
from app.services.chat import stream_chat

chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@chat_router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> StreamingResponse:
    generator = stream_chat(user=user, message=request.message)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
