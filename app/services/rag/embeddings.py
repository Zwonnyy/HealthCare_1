import logging

from google import genai
from google.genai import types

from app.core import config

logger = logging.getLogger(__name__)
# text-embedding-004 is unavailable in this region; gemini-embedding-001 with
# output_dimensionality=768 is compatible with the 768-dim Qdrant collections.
_EMBED_MODEL = "gemini-embedding-001"
_EMBED_DIM = 768


async def embed(text: str) -> list[float] | None:
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = await client.aio.models.embed_content(
            model=_EMBED_MODEL,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=_EMBED_DIM),
        )
        return list(response.embeddings[0].values)
    except Exception as e:
        logger.warning("Embedding failed: %s", e)
        return None
