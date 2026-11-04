import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db_session
from app.main import create_app
from app.models.user import User, UserRole
from app.api.deps import get_current_active_user

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db_session():
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    import os
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest_asyncio.fixture
async def db_session(setup_database):
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    import uuid
    user = User(
        sub=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_client(db_session, test_user):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def viewer_user(db_session):
    viewer = User(
        sub="viewer-sub",
        email="viewer@example.com",
        username="viewer",
        role=UserRole.VIEWER,
    )
    db_session.add(viewer)
    await db_session.commit()
    await db_session.refresh(viewer)
    return viewer


@pytest_asyncio.fixture
async def viewer_client(db_session, viewer_user):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[get_current_active_user] = lambda: viewer_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
