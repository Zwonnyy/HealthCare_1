import asyncio
import os
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest
from tortoise import generate_config
from tortoise.contrib.test import finalizer, initializer

from app.core.db.databases import TORTOISE_APP_MODELS

TEST_BASE_URL = "http://test"
TEST_DB_LABEL = "models"
TEST_DB_TZ = "Asia/Seoul"


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def setex(self, name: str, time: int, value: str) -> None:
        self._store[name] = value

    async def get(self, name: str) -> str | None:
        return self._store.get(name)

    async def delete(self, name: str) -> None:
        self._store.pop(name, None)


def get_test_db_config() -> dict[str, Any]:
    tortoise_config = generate_config(
        db_url=os.getenv("TEST_DB_URL", "sqlite://:memory:"),
        app_modules={TEST_DB_LABEL: TORTOISE_APP_MODELS},
        connection_label=TEST_DB_LABEL,
        testing=True,
    )
    tortoise_config["timezone"] = TEST_DB_TZ

    return tortoise_config


@pytest.fixture(scope="session", autouse=True)
def initialize(request: FixtureRequest) -> Generator[None, None]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    fake_redis = FakeRedis()
    with (
        patch("tortoise.contrib.test.getDBConfig", Mock(return_value=get_test_db_config())),
        patch("app.services.jwt.redis_client", fake_redis),
    ):
        initializer(modules=TORTOISE_APP_MODELS)
        yield
        finalizer()
        loop.close()


@pytest_asyncio.fixture(autouse=True, scope="session")  # type: ignore[type-var]
def event_loop() -> None:
    pass
