# app/db.py
import os
import asyncio
import ssl
from urllib.parse import quote_plus, urlparse, urlunparse, parse_qsl, urlencode
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

load_dotenv()

def sanitize_database_url(raw_url: str) -> str:
    """
    Remove URL query params that asyncpg does not accept (e.g. sslmode, connect_timeout).
    Return sanitized URL string.
    """
    parsed = urlparse(raw_url)
    if not parsed.scheme:
        return raw_url

    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for bad in ("sslmode", "connect_timeout", "connect-timeout", "connecttimeout", "connecttimeout_ms"):
        q.pop(bad, None)

    new_query = urlencode(q, doseq=True)
    sanitized = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )
    return sanitized

def build_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL")
    if raw_url and "@" in raw_url:
        return sanitize_database_url(raw_url)

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "resumerag")
    encoded_pw = quote_plus(password)
    return f"postgresql+asyncpg://{user}:{encoded_pw}@{host}:{port}/{name}"

DATABASE_URL = build_database_url()

def build_connect_args() -> dict:
    """
    Build connect_args for SQLAlchemy -> asyncpg.
    asyncpg expects:
      - ssl: an SSLContext (or True)
      - timeout: float seconds for connect timeout
    """
    connect_args = {}

    db_host = os.getenv("DB_HOST", "")
    sslmode = os.getenv("DB_SSLMODE", "").lower()  # "require" etc.
    timeout_env = os.getenv("DB_CONNECT_TIMEOUT", "")  # seconds (string)

    # Decide SSL use: explicit env var or RDS hostname heuristic
    use_ssl = False
    if sslmode in ("require", "verify-full", "verify-ca"):
        use_ssl = True
    elif "rds.amazonaws.com" in (db_host or "") and not sslmode:
        use_ssl = True

    if use_ssl:
        ssl_ctx = ssl.create_default_context()
        connect_args["ssl"] = ssl_ctx

    # asyncpg uses 'timeout' (float) for connection attempts
    try:
        connect_args["timeout"] = float(timeout_env) if timeout_env else 20.0
    except ValueError:
        connect_args["timeout"] = 20.0

    return connect_args

CONNECT_ARGS = build_connect_args()

# Engine & session
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
    """
    Initialize database tables with retry logic.
    If DATABASE_URL was provided with unsupported query params, they've been sanitized.
    """
    # Log masked connection info to help debug (do not print secrets)
    try:
        parsed = urlparse(DATABASE_URL)
        host = parsed.hostname or os.getenv("DB_HOST", "")
        port = parsed.port or os.getenv("DB_PORT", "5432")
        print(f"Attempting DB connect to {host}:{port} (masked).")
    except Exception:
        print("Attempting DB connect (masked host info).")

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
