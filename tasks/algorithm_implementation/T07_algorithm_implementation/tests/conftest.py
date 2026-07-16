import pytest
import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    try:
        from main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    except ImportError:
        pytest.skip("main.py not found — app not implemented yet")
