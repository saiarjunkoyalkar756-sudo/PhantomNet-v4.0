import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend_api.iam_service.main import app
from backend_api.shared.database import Base, get_db

# Create an async SQLite test engine
async_test_db_url = "sqlite+aiosqlite:///./test.db"
async_test_engine = create_async_engine(async_test_db_url, connect_args={"check_same_thread": False})
AsyncTestingSessionLocal = async_sessionmaker(
    bind=async_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="function")
def client():
    # Setup: Create tables synchronously via asyncio
    async def create_tables():
        async with async_test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If a loop is already running, run the coroutine in it
            loop.create_task(create_tables())
        else:
            loop.run_until_complete(create_tables())
    except Exception:
        asyncio.run(create_tables())
    
    # Configure dependency overrides
    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
                
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
        
    # Teardown: Clean up overrides and drop tables
    app.dependency_overrides.clear()
    
    async def drop_tables():
        async with async_test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(drop_tables())
        else:
            loop.run_until_complete(drop_tables())
    except Exception:
        asyncio.run(drop_tables())
