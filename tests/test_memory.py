"""Unit tests for memory module."""

import pytest
import tempfile
import os
from pathlib import Path

from src.memory import ConversationMemory


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_instance(temp_db):
    """Create a memory instance with temporary database."""
    return ConversationMemory(db_path=temp_db)


def test_create_session(memory_instance):
    """Test session creation."""
    session_id = "test-session-1"
    
    # Create session
    result = memory_instance.create_session(session_id)
    assert result is True
    
    # Try to create again (should return False)
    result = memory_instance.create_session(session_id)
    assert result is False


def test_add_message(memory_instance):
    """Test adding messages."""
    session_id = "test-session-1"
    memory_instance.create_session(session_id)
    
    # Add user message
    memory_instance.add_message(session_id, "user", "Hello")
    
    # Add assistant message
    memory_instance.add_message(session_id, "assistant", "Hi there!")
    
    # Retrieve messages
    messages = memory_instance.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"


def test_get_messages(memory_instance):
    """Test retrieving messages."""
    session_id = "test-session-1"
    memory_instance.create_session(session_id)
    
    # Add multiple messages
    for i in range(5):
        role = "user" if i % 2 == 0 else "assistant"
        memory_instance.add_message(session_id, role, f"Message {i}")
    
    # Get all messages
    messages = memory_instance.get_messages(session_id)
    assert len(messages) == 5
    
    # Get limited messages
    messages = memory_instance.get_messages(session_id, limit=3)
    assert len(messages) == 3


def test_get_session_info(memory_instance):
    """Test getting session information."""
    session_id = "test-session-1"
    metadata = {"key": "value"}
    
    memory_instance.create_session(session_id, metadata)
    memory_instance.add_message(session_id, "user", "Test message")
    
    info = memory_instance.get_session_info(session_id)
    assert info is not None
    assert info["session_id"] == session_id
    assert info["message_count"] == 1
    assert info["metadata"] == metadata


def test_list_sessions(memory_instance):
    """Test listing sessions."""
    # Create multiple sessions
    for i in range(3):
        session_id = f"test-session-{i}"
        memory_instance.create_session(session_id)
        memory_instance.add_message(session_id, "user", f"Message {i}")
    
    # List sessions
    sessions = memory_instance.list_sessions()
    assert len(sessions) == 3


def test_delete_session(memory_instance):
    """Test deleting a session."""
    session_id = "test-session-1"
    memory_instance.create_session(session_id)
    memory_instance.add_message(session_id, "user", "Test")
    
    # Delete session
    result = memory_instance.delete_session(session_id)
    assert result is True
    
    # Verify deletion
    info = memory_instance.get_session_info(session_id)
    assert info is None
    
    # Try to delete non-existent session
    result = memory_instance.delete_session("non-existent")
    assert result is False
