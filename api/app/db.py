import os
import asyncio
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

# --------------------------------------------------------------------------
# Build DATABASE_URL safely (handles special chars, adds sslmode & timeout)
# --------------------------------------------------------------------------
def build_database_url():
    raw_url = os.getenv("DATABASE_URL")
    if raw_url and "@" in raw_url:
        # Assume it's a full URL already (e.g., in Render)
        return raw_url

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "resumerag")
    sslmode = os.getenv("DB_SSLMODE", "require" if "rds.amazonaws.com" in host else "disable")
    connect_timeout = os.getenv("DB_CONNECT_TIMEOUT", "20")

    encoded_pw = quote_plus(password)
    return (
        f"postgresql+asyncpg://{user}:{encoded_pw}@{host}:{port}/{name}"
        f"?sslmode={sslmode}&connect_timeout={connect_timeout}"
    )


DATABASE_URL = build_database_url()

# --------------------------------------------------------------------------
# SQLAlchemy Engine & Session Configuration
# --------------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,  # safe for async + Render’s short-lived connections
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


# --------------------------------------------------------------------------
# Dependency: Get DB Session
# --------------------------------------------------------------------------
async def get_db():
    """Provide an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# --------------------------------------------------------------------------
# Safe DB Initialization with Retries (for Render / Cloud startup)
# --------------------------------------------------------------------------
async def init_db(retries: int = 5, delay: int = 3):
    """Initialize database tables with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database initialized successfully.")
            return
        except Exception as e:
            print(f"⚠️  DB connection failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                print("❌ Could not connect to database after retries. Exiting.")
                raise
