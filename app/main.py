import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.apis.v1 import v1_routers
from app.core import config
from app.core.db.databases import initialize_tortoise

logger = logging.getLogger(__name__)


async def _init_rag_background() -> None:
    try:
        from app.models.records import MedicalRecord
        from app.services.rag.client import init_collections
        from app.services.rag.drug_rag import seed_drug_info
        from app.services.rag.guideline_rag import seed_guidelines
        from app.services.rag.patient_rag import index_record

        await init_collections()
        await seed_drug_info()
        await seed_guidelines()

        # Index existing records in background
        records = await MedicalRecord.all()
        for record in records:
            await index_record(
                record_id=record.id,
                patient_id=record.patient_id,
                diagnosis=record.diagnosis,
                symptoms=record.symptoms,
                notes=record.notes,
                visited_at=str(record.visited_at),
            )
        logger.info("RAG initialization complete")
    except Exception as e:
        logger.warning("RAG init failed (non-fatal): %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    rag_task = asyncio.create_task(_init_rag_background())
    try:
        yield
    finally:
        if not rag_task.done():
            rag_task.cancel()


app = FastAPI(
    default_response_class=ORJSONResponse,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
initialize_tortoise(app)
app.include_router(v1_routers)
Path(config.MEDIA_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=config.MEDIA_DIR), name="media")
