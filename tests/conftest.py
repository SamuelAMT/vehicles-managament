from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base
from app.core.security import hash_password
from app.dependencies.db import get_db
from app.main import app
from app.models.user import User  # noqa: F401
from app.models.vehicle import Vehicle  # noqa: F401

engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args={"statement_cache_size": 0},
)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
def mock_usd_rate():
    with patch("app.services.vehicle.get_usd_to_brl", new=AsyncMock(return_value=5.0)):
        yield


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True, scope="function")
async def truncate_tables():
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE vehicles, users RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db(truncate_tables) -> AsyncSession:
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(username="admin", password_hash=hash_password("admin123"), role="ADMIN")
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def regular_user(db: AsyncSession) -> User:
    user = User(username="user1", password_hash=hash_password("user123"), role="USER")
    db.add(user)
    await db.commit()
    return user


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    r = await client.post("/auth/token", json={"username": "admin", "password": "admin123"})
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, regular_user: User) -> str:
    r = await client.post("/auth/token", json={"username": "user1", "password": "user123"})
    return r.json()["access_token"]
