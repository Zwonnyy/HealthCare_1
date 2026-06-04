import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core import config

logger = logging.getLogger(__name__)

EMBEDDING_SIZE = 768
COLLECTIONS = {
    "drug_info": VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
    "patient_records": VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
    "medical_guidelines": VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
}

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    return _client


async def init_collections() -> None:
    client = get_client()
    for name, params in COLLECTIONS.items():
        try:
            exists = await client.collection_exists(name)
            if not exists:
                await client.create_collection(collection_name=name, vectors_config=params)
                logger.info("Created Qdrant collection: %s", name)
        except Exception as e:
            logger.warning("Failed to init Qdrant collection %s: %s", name, e)
