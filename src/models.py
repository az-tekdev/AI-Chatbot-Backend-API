"""Pydantic models for API request and response schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Single chat message model."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message", min_length=1)
    session_id: str = Field(..., description="Session identifier for conversation continuity")
    stream: bool = Field(default=False, description="Whether to stream the response")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Override temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Override max tokens")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session identifier")
    tools_used: List[str] = Field(default_factory=list, description="List of tools invoked")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")


class SessionCreate(BaseModel):
    """Request model for creating a new session."""
    session_id: Optional[str] = Field(None, description="Optional custom session ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session metadata")


class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str = Field(..., description="Session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    message_count: int = Field(..., description="Number of messages in session")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")


class ToolInfo(BaseModel):
    """Information about an available tool."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters schema")


class ToolsResponse(BaseModel):
    """Response model for tools endpoint."""
    tools: List[ToolInfo] = Field(..., description="List of available tools")
    count: int = Field(..., description="Number of tools")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    code: Optional[str] = Field(None, description="Error code")
