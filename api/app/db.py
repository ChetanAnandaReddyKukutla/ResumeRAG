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
        # Strip sslmode from URL if present (we'll manage SSL via connect_args)
        if "sslmode=" in raw_url:
            base, _, query = raw_url.partition("?")
            params = [p for p in query.split("&") if not p.startswith("sslmode=")]
            new_q = "&".join([p for p in params if p])
            return f"{base}?{new_q}" if new_q else base
        return raw_url

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "resumerag")
    encoded_pw = quote_plus(password)

    return f"postgresql+asyncpg://{user}:{encoded_pw}@{host}:{port}/{name}"

DATABASE_URL = build_database_url()

def build_connect_args():
    """
    Build connect_args for SQLAlchemy -> asyncpg.
    asyncpg expects:
      - ssl: an SSLContext (or True)
      - timeout: a float (seconds) for connect timeout
    Do NOT pass 'sslmode' or 'connect_timeout' here.
    """
    connect_args = {}

    db_host = os.getenv("DB_HOST", "")
    sslmode = os.getenv("DB_SSLMODE", "").lower()  # e.g. "require" or ""
    timeout = os.getenv("DB_CONNECT_TIMEOUT", "")   # seconds (string)

    # Determine whether to use SSL (default to True for RDS hostnames)
    use_ssl = False
    if sslmode in ("require", "verify-full", "verify-ca"):
        use_ssl = True
    elif "rds.amazonaws.com" in (db_host or "") and not sslmode:
        use_ssl = True

    if use_ssl:
        # create default context which will verify server certs
        ssl_ctx = ssl.create_default_context()
        connect_args["ssl"] = ssl_ctx

    # asyncpg uses 'timeout' (float) for connect timeout
    if timeout:
        try:
            connect_args["timeout"] = float(timeout)
        except ValueError:
            # fallback to a sensible default
            connect_args["timeout"] = 20.0
    else:
        connect_args["timeout"] = 20.0

    return connect_args

CONNECT_ARGS = build_connect_args()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
    connect_args=CONNECT_ARGS,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

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
