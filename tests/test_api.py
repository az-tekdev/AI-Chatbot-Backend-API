"""Unit tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os

from src.main import app
from src.memory import ConversationMemory


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_memory():
    """Create mock memory instance."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    memory = ConversationMemory(db_path=db_path)
    
    yield memory
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_tools(client):
    """Test tools listing endpoint."""
    # Mock API key verification
    with patch("src.main.verify_api_key", return_value=True):
        response = client.get("/tools")
        assert response.status_code == 200
        assert "tools" in response.json()
        assert "count" in response.json()


def test_create_session(client):
    """Test session creation endpoint."""
    with patch("src.main.verify_api_key", return_value=True):
        response = client.post(
            "/sessions",
            json={"session_id": "test-session-123"}
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == "test-session-123"


def test_chat_endpoint(client):
    """Test chat endpoint."""
    with patch("src.main.verify_api_key", return_value=True):
        # Mock agent execution
        with patch("src.main.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.run.return_value = {
                "output": "Test response",
                "tools_used": [],
                "intermediate_steps": []
            }
            mock_get_agent.return_value = mock_agent
            
            response = client.post(
                "/chat",
                json={
                    "message": "Hello",
                    "session_id": "test-session-123"
                }
            )
            
            assert response.status_code == 200
            assert "response" in response.json()
            assert response.json()["session_id"] == "test-session-123"


def test_list_sessions(client):
    """Test listing sessions endpoint."""
    with patch("src.main.verify_api_key", return_value=True):
        response = client.get("/sessions")
        assert response.status_code == 200
        assert "sessions" in response.json()
        assert "total" in response.json()
