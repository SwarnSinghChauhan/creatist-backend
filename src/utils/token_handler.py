from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import jwt
from pydantic import BaseModel, Field
from pytz import timezone

from src.models import UserModel
from src.utils.log import log

if TYPE_CHECKING:
    pass


class Token(BaseModel):
    sub: UUID
    email: str
    name: str
    iat: int = Field(
        default_factory=lambda: int(datetime.now(timezone("UTC")).timestamp())
    )
    exp: int

    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
        }


class TokenHandler:
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm

    def create_access_token(self, user: UserModel, expire_in: int = 360) -> str:
        log.debug("Creating access token for user: %s", user.id)
        payload = Token(
            sub=user.id,
            email=user.email,
            name="%s" % user.name,
            exp=int(
                (
                    datetime.now(timezone("UTC")) + timedelta(seconds=expire_in)
                ).timestamp()
            ),
        )
        token = jwt.encode(
            payload.model_dump(mode="json"), self.secret, algorithm=self.algorithm
        )
        log.info("Access token created for user: %s", user.id)
        return token

    def validate_token(self, token: str) -> Optional[Token]:
        log.debug("Validating token")
        try:
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            log.info("Token successfully validated")
            return Token(**decoded)
        except jwt.ExpiredSignatureError:
            log.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            log.error("Invalid token provided")
            return None

    def decode_token(self, token: str) -> Optional[Token]:
        log.debug("Decoding token")
        try:
            decoded = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            log.info("Token successfully decoded")
            return Token(**decoded)
        except jwt.InvalidTokenError:
            log.error("Token decoding failed due to invalid token", exc_info=True)
            raise
