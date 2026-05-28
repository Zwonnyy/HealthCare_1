from typing import Literal, overload

from fastapi import HTTPException

from app.core import config
from app.core.jwt.exceptions import ExpiredTokenError, TokenError
from app.core.jwt.tokens import AccessToken, RefreshToken
from app.core.redis import redis_client
from app.models.users import User

_REFRESH_TOKEN_PREFIX = "refresh:"


class JwtService:
    access_token_class = AccessToken
    refresh_token_class = RefreshToken

    def create_access_token(self, user: User) -> AccessToken:
        return self.access_token_class.for_user(user)

    def create_refresh_token(self, user: User) -> RefreshToken:
        return self.refresh_token_class.for_user(user)

    @overload
    def verify_jwt(self, token: str, token_type: Literal["access"]) -> AccessToken: ...

    @overload
    def verify_jwt(self, token: str, token_type: Literal["refresh"]) -> RefreshToken: ...

    def verify_jwt(self, token: str, token_type: Literal["access", "refresh"]) -> AccessToken | RefreshToken:
        token_class: type[AccessToken | RefreshToken] = (
            self.access_token_class if token_type == "access" else self.refresh_token_class
        )
        try:
            return token_class(token=token)
        except ExpiredTokenError as err:
            raise HTTPException(status_code=401, detail=f"{token_type} token has expired.") from err
        except TokenError as err:
            raise HTTPException(status_code=400, detail="Provided invalid token.") from err

    async def store_refresh_token(self, refresh_token: RefreshToken) -> None:
        jti = refresh_token["jti"]
        user_id = refresh_token["user_id"]
        await redis_client.setex(
            name=f"{_REFRESH_TOKEN_PREFIX}{jti}",
            time=config.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            value=str(user_id),
        )

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        try:
            verified = self.verify_jwt(token=refresh_token, token_type="refresh")
            await redis_client.delete(f"{_REFRESH_TOKEN_PREFIX}{verified['jti']}")
        except HTTPException:
            pass

    async def refresh_jwt(self, refresh_token: str) -> AccessToken:
        verified_rt = self.verify_jwt(token=refresh_token, token_type="refresh")
        jti = verified_rt["jti"]
        stored = await redis_client.get(f"{_REFRESH_TOKEN_PREFIX}{jti}")
        if not stored:
            raise HTTPException(status_code=401, detail="Refresh token has been revoked or expired.")
        return verified_rt.access_token

    async def issue_jwt_pair(self, user: User) -> dict[str, AccessToken | RefreshToken]:
        rt = self.create_refresh_token(user)
        at = rt.access_token
        await self.store_refresh_token(rt)
        return {"access_token": at, "refresh_token": rt}
