from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.drug_interactions import DrugInteractionResponse
from app.models.users import User
from app.services.drug_interactions import DrugInteractionService

drug_interaction_router = APIRouter(prefix="/records", tags=["drug-interactions"])


@drug_interaction_router.post(
    "/{record_id}/interactions", response_model=DrugInteractionResponse, status_code=status.HTTP_200_OK
)
async def check_interactions(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DrugInteractionService, Depends(DrugInteractionService)],
) -> Response:
    result = await service.check(user=user, record_id=record_id)
    return Response(DrugInteractionResponse.model_validate(result).model_dump(), status_code=status.HTTP_200_OK)


@drug_interaction_router.get(
    "/{record_id}/interactions", response_model=DrugInteractionResponse | None, status_code=status.HTTP_200_OK
)
async def get_latest_interaction(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[DrugInteractionService, Depends(DrugInteractionService)],
) -> Response:
    result = await service.get_latest(user=user, record_id=record_id)
    return Response(
        DrugInteractionResponse.model_validate(result).model_dump() if result else None,
        status_code=status.HTTP_200_OK,
    )
