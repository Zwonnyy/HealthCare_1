import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from app.dependencies.security import get_doctor_user
from app.models.users import User

logger = logging.getLogger(__name__)

rag_router = APIRouter(prefix="/rag", tags=["RAG"])


@rag_router.get("/stats")
async def get_rag_stats(
    _doctor: Annotated[User, Depends(get_doctor_user)],
) -> dict:
    """Return document counts for all RAG collections (doctor only)."""
    from app.services.rag.client import COLLECTIONS, get_client

    client = get_client()
    stats: dict[str, int] = {}
    for collection_name in COLLECTIONS:
        try:
            result = await client.count(collection_name=collection_name)
            stats[collection_name] = result.count
        except Exception as e:
            logger.warning("Failed to count collection %s: %s", collection_name, e)
            stats[collection_name] = -1

    return {"collections": stats}


@rag_router.post("/reseed", status_code=status.HTTP_200_OK)
async def reseed_rag(
    _doctor: Annotated[User, Depends(get_doctor_user)],
) -> dict:
    """Re-seed drug_info and medical_guidelines collections (doctor only)."""
    from app.services.rag.client import get_client
    from app.services.rag.drug_rag import DRUG_DATA, seed_drug_info
    from app.services.rag.guideline_rag import GUIDELINE_DATA, seed_guidelines

    client = get_client()

    # Clear existing collections
    for collection_name in ("drug_info", "medical_guidelines"):
        try:
            exists = await client.collection_exists(collection_name)
            if exists:
                await client.delete_collection(collection_name)
                logger.info("Deleted Qdrant collection: %s", collection_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to clear collection {collection_name}: {e}",
            ) from e

    # Re-initialise collections and seed
    try:
        from app.services.rag.client import init_collections

        await init_collections()
        await seed_drug_info()
        await seed_guidelines()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reseed failed: {e}",
        ) from e

    return {
        "message": "Reseed complete",
        "drug_info_docs": len(DRUG_DATA),
        "guidelines_docs": len(GUIDELINE_DATA),
    }
