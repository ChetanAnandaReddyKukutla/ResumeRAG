import os
import sys
from pathlib import Path
import pytest
from io import BytesIO
from fastapi import UploadFile
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Test environment flags MUST be set before importing the FastAPI app so that
# global singletons (rate limiter, tracing, logging) pick them up correctly.
# ---------------------------------------------------------------------------
os.environ.setdefault("TEST_DISABLE_RATE_LIMIT", "1")  # Disable Redis rate limiter
os.environ.setdefault("TESTING", "1")  # Signal test mode (disable tracing, root logging noise)
os.environ.setdefault("OTEL_SDK_DISABLED", "1")  # Extra guard to silence OpenTelemetry exporter
os.environ["MAX_FAILED_ATTEMPTS"] = "5"  # Ensure lockout threshold stable for tests

# Insert api directory before importing app
ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / 'api'
APP_PKG_DIR = API_DIR / 'app'
for p in (API_DIR, APP_PKG_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from app.main import app  # type: ignore
except ModuleNotFoundError:
    # Fallback dynamic import when package import fails
    import importlib.util
    main_path = APP_PKG_DIR / 'main.py'
    spec = importlib.util.spec_from_file_location('app.main', main_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError("Failed to load app.main spec for tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    app = module.app  # type: ignore


@pytest.fixture
def upload_file_factory():
    """Factory to create UploadFile objects without mutating read-only attrs.

    FastAPI's UploadFile will infer content_type from the underlying SpooledTemporaryFile; for tests we only
    need filename & bytes. If code relies on content_type, tests should pass it where API expects via form-data.
    """
    def _create(filename: str, content: bytes, content_type: str = "application/octet-stream"):
        uf = UploadFile(filename=filename, file=BytesIO(content))
        # Attach a private attribute used only in tests
        setattr(uf, "_test_content_type", content_type)
        return uf
    return _create


@pytest.fixture
def client(event_loop):  # rely on pytest-asyncio provided event_loop
    """Shared client fixture returning an AsyncClient bound to already running loop.

    Tests marked with @pytest.mark.asyncio can await methods on this client.
    """
    ac = AsyncClient(app=app, base_url="http://test")
    event_loop.run_until_complete(ac.__aenter__())
    yield ac
    event_loop.run_until_complete(ac.__aexit__(None, None, None))
