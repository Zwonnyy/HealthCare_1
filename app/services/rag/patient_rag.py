import logging

from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from app.services.rag.client import get_client
from app.services.rag.embeddings import embed

logger = logging.getLogger(__name__)

_COLLECTION = "patient_records"


async def index_record(
    record_id: int,
    patient_id: int,
    diagnosis: str,
    symptoms: str,
    notes: str | None,
    visited_at: str,
) -> None:
    text = f"진단: {diagnosis}\n증상: {symptoms}"
    vector = await embed(text)
    if vector is None:
        return

    client = get_client()
    try:
        await client.upsert(
            collection_name=_COLLECTION,
            points=[
                PointStruct(
                    id=record_id,
                    vector=vector,
                    payload={
                        "record_id": record_id,
                        "patient_id": patient_id,
                        "diagnosis": diagnosis,
                        "symptoms": symptoms,
                        "notes": notes or "",
                        "visited_at": visited_at,
                    },
                )
            ],
        )
        logger.info("Indexed patient record %d for patient %d", record_id, patient_id)
    except Exception as e:
        logger.warning("Failed to index patient record %d: %s", record_id, e)


async def search_patient_history(patient_id: int, query: str, limit: int = 3) -> str:
    vector = await embed(query)
    if vector is None:
        return ""

    client = get_client()
    try:
        hits = await client.search(
            collection_name=_COLLECTION,
            query_vector=vector,
            query_filter=Filter(
                must=[FieldCondition(key="patient_id", match=MatchValue(value=patient_id))]
            ),
            limit=limit,
            score_threshold=0.4,
        )
    except Exception as e:
        logger.warning("Patient history search failed for patient %d: %s", patient_id, e)
        return ""

    if not hits:
        return ""

    lines = []
    for hit in hits:
        payload = hit.payload or {}
        lines.append(
            f"- 방문일: {payload.get('visited_at', '미상')}, "
            f"진단: {payload.get('diagnosis', '')}, "
            f"증상: {payload.get('symptoms', '')}"
            + (f", 메모: {payload.get('notes')}" if payload.get("notes") else "")
        )
    return "\n".join(lines)
