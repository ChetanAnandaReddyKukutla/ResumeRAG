# app/db.py
import os
import asyncio
import ssl
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

def sanitize_database_url(raw_url: str) -> str:
    """
    Remove unsupported query params (like sslmode) from DATABASE_URL.
    """
    parsed = urlparse(raw_url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for bad in ("sslmode", "connect_timeout", "connecttimeout", "connect-timeout"):
        q.pop(bad, None)
    new_query = urlencode(q, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

# --- Use only DATABASE_URL from environment ---
raw_url = os.getenv("DATABASE_URL")
if not raw_url:
    raise RuntimeError("❌ DATABASE_URL not found in environment!")

DATABASE_URL = sanitize_database_url(raw_url)

# --- SSL for AWS RDS (enabled automatically for .rds.amazonaws.com hosts) ---
def build_connect_args():
    connect_args = {}
    ssl_ctx = None
    if "rds.amazonaws.com" in DATABASE_URL:
        ssl_ctx = ssl.create_default_context()
    if ssl_ctx:
        connect_args["ssl"] = ssl_ctx
    connect_args["timeout"] = 30.0
    return connect_args

CONNECT_ARGS = build_connect_args()

# --- SQLAlchemy async engine & session setup ---
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

# --- Database initialization with retry ---
async def init_db(retries: int = 5, delay: int = 3):
    parsed = urlparse(DATABASE_URL)
    print(f"Attempting DB connect to {parsed.hostname}:{parsed.port} (masked).")

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
