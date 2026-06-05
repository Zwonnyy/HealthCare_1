from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from starlette import status
from tortoise.transactions import in_transaction

from app.core import config
from app.core.utils.common import normalize_phone_number
from app.core.utils.security import hash_password, verify_password
from app.dtos.users import UserUpdateRequest
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.auth import AuthService


class UserManageService:
    def __init__(self):
        self.repo = UserRepository()
        self.auth_service = AuthService()

    async def update_user(self, user: User, data: UserUpdateRequest) -> User:
        if data.email:
            await self.auth_service.check_email_exists(data.email)
        if data.phone_number:
            normalized_phone_number = normalize_phone_number(data.phone_number)
            await self.auth_service.check_phone_number_exists(normalized_phone_number)
            data.phone_number = normalized_phone_number

        update_dict = data.model_dump(exclude_none=True, exclude={"current_password", "new_password"})

        if data.new_password:
            if not data.current_password:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호를 입력해주세요.")
            if not verify_password(data.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 올바르지 않습니다."
                )
            update_dict["hashed_password"] = hash_password(data.new_password)

        async with in_transaction():
            await self.repo.update_instance(user=user, data=update_dict)
            await user.refresh_from_db()
        return user

    async def update_profile_image(self, user: User, image: UploadFile) -> User:
        if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JPG, PNG, WEBP 이미지만 업로드할 수 있습니다.",
            )

        contents = await image.read()
        if len(contents) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="이미지는 2MB 이하만 업로드할 수 있습니다."
            )

        extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }[image.content_type]
        upload_dir = Path(config.MEDIA_DIR) / "profile-images"
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"user-{user.id}-{uuid4().hex}{extension}"
        file_path = upload_dir / filename
        file_path.write_bytes(contents)

        image_url = f"/media/profile-images/{filename}"
        async with in_transaction():
            await self.repo.update_instance(user=user, data={"profile_image_url": image_url})
            await user.refresh_from_db()
        return user
