import pytest
import httpx
from scripts.api_server import app

@pytest.fixture(scope="module")
def anyio_backend():
    """Fixture to enable asynchronous testing with anyio."""
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    """
    Asynchronous test client for the FastAPI application.
    Yields a clean client that can make requests to the app without running a server.
    """
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac