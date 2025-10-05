# app/db.py
import os
import asyncio
import ssl
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

def build_database_url():
    raw_url = os.getenv("DATABASE_URL")
    if raw_url and "@" in raw_url:
        # Full URL supplied by host — ensure it does NOT include sslmode=...
        # (we will handle SSL via connect_args below)
        # If the URL contains sslmode query, strip it.
        if "sslmode=" in raw_url:
            # it's okay to strip sslmode here so SQLAlchemy/asyncpg won't receive it
            base, _, query = raw_url.partition("?")
            # rebuild query without sslmode param
            params = [p for p in query.split("&") if not p.startswith("sslmode=")]
            new_q = "&".join(params) if params else ""
            return f"{base}?{new_q}" if new_q else base
        return raw_url

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "resumerag")
    encoded_pw = quote_plus(password)

    # Note: Do NOT append sslmode here. We'll pass SSL via connect_args below.
    return f"postgresql+asyncpg://{user}:{encoded_pw}@{host}:{port}/{name}"

DATABASE_URL = build_database_url()

# Build connect_args for asyncpg
def build_connect_args():
    connect_args = {}
    # asyncpg accepts 'ssl' as an SSLContext (or True for default), and 'timeout' as seconds.
    db_host = os.getenv("DB_HOST", "")
    sslmode = os.getenv("DB_SSLMODE", "").lower()  # expected values: "require", "disable", ""
    timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "20"))

    # If ssl is requested (e.g., for RDS), create a default SSLContext.
    if sslmode in ("require", "verify-full", "verify-ca") or ("rds.amazonaws.com" in db_host and not sslmode):
        # Use default cert verification. If you need to skip verification (not recommended),
        # use ssl._create_unverified_context() but do not do this in production.
        ssl_ctx = ssl.create_default_context()
        connect_args["ssl"] = ssl_ctx

    # asyncpg accepts 'timeout' for connection attempt
    connect_args["timeout"] = timeout

    return connect_args

CONNECT_ARGS = build_connect_args()

# --------------------------------------------------------------------------
# Engine & session
# --------------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
    connect_args=CONNECT_ARGS,  # pass SSLContext and timeout here
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --------------------------------------------------------------------------
# Dependency: Get DB Session
# --------------------------------------------------------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# --------------------------------------------------------------------------
# Safe DB Initialization with Retries
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
