import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/resumerag")

# Use NullPool to avoid connection reuse across rapid test client startup/shutdown
# which has been causing asyncpg InterfaceError "another operation is in progress"
# under heavy sequential test execution on Windows. Each session will acquire its
# own fresh connection.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    """Provide an async DB session.

    Explicit transaction control is left to the calling code. This avoids
    double-commit patterns (endpoint commits plus dependency auto-commit) that
    were triggering asyncpg "another operation is in progress" InterfaceErrors
    when rapid sequential requests occurred in tests. Callers should commit on
    success and rollback on handled failures where persistence is required.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # Roll back unhandled exceptions to leave database consistent
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
