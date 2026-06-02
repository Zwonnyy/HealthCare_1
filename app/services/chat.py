import json
from collections.abc import AsyncGenerator

from google import genai
from google.genai import types

from app.core import config
from app.models.users import User

_CHAT_SYSTEM_PROMPT = (
    "당신은 MediGuide AI 헬스케어 어시스턴트입니다. "
    "복약, 증상, 건강 관리에 관한 질문에 친절하고 정확하게 답변합니다. "
    "모든 답변은 한국어로 작성하며, 의학적 결정은 반드시 담당 의사와 상담하도록 안내합니다. "
    "단순 건강 정보 제공은 가능하지만 진단이나 처방은 하지 않습니다."
)


async def stream_chat(user: User, message: str) -> AsyncGenerator[str, None]:
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        async for chunk in await client.aio.models.generate_content_stream(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=_CHAT_SYSTEM_PROMPT),
            contents=message,
        ):
            if chunk.text:
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk.text}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
