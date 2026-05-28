from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_doctor_user, get_request_user
from app.dtos.users import PatientSearchResult, UserInfoResponse, UserUpdateRequest
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.users import UserManageService

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def user_me_info(
    user: Annotated[User, Depends(get_request_user)],
) -> Response:
    return Response(UserInfoResponse.model_validate(user).model_dump(), status_code=status.HTTP_200_OK)


@user_router.patch("/me", response_model=UserInfoResponse, status_code=status.HTTP_200_OK)
async def update_user_me_info(
    update_data: UserUpdateRequest,
    user: Annotated[User, Depends(get_request_user)],
    user_manage_service: Annotated[UserManageService, Depends(UserManageService)],
) -> Response:
    updated_user = await user_manage_service.update_user(user=user, data=update_data)
    return Response(UserInfoResponse.model_validate(updated_user).model_dump(), status_code=status.HTTP_200_OK)


@user_router.get("/patients/search", response_model=list[PatientSearchResult], status_code=status.HTTP_200_OK)
async def search_patients(
    q: Annotated[str, Query(min_length=1)],
    _: Annotated[User, Depends(get_doctor_user)],
    user_repo: Annotated[UserRepository, Depends(UserRepository)],
) -> Response:
    patients = await user_repo.search_patients(q)
    return Response(
        [PatientSearchResult.model_validate(p).model_dump() for p in patients],
        status_code=status.HTTP_200_OK,
    )
