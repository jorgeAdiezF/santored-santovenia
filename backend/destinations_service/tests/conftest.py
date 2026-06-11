import sys
import os
import importlib.util

_SERVICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BACKEND_DIR = os.path.abspath(os.path.join(_SERVICE_DIR, ".."))

if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
if _SERVICE_DIR not in sys.path:
    sys.path.insert(0, _SERVICE_DIR)

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from shared.database import Base, get_db
from shared.auth import get_current_user
from shared.models import User, Role

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_MODULE_NAME = "destinations_service_main"


def _get_app():
    if _MODULE_NAME not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            _MODULE_NAME, os.path.join(_SERVICE_DIR, "main.py")
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[_MODULE_NAME] = mod
        spec.loader.exec_module(mod)
    return sys.modules[_MODULE_NAME].app


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def make_mock_user(role_name: str = "admin") -> User:
    return User(
        id=1,
        username="testuser",
        name="Test User",
        email="test@test.com",
        active=True,
        role=Role(id=1, name=role_name),
    )


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    app = _get_app()

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: make_mock_user()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
