"""FastAPI application entry point."""

import logging
import uuid
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from src.config import settings
from src.models import (
    ChatRequest, ChatResponse, SessionCreate, SessionResponse,
    SessionListResponse, ToolsResponse, ErrorResponse
)
from src.agent import get_agent
from src.memory import memory
from src.tools import get_tool_info

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key security (if enabled)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify API key if authentication is enabled.
    
    Args:
        x_api_key: API key from header
        
    Returns:
        True if valid or auth disabled
        
    Raises:
        HTTPException if auth enabled and key invalid
    """
    if not settings.enable_auth:
        return True
    
    if not settings.api_key:
        logger.warning("API key authentication enabled but no API key configured")
        return True
    
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    from src.config import validate_settings
    validate_settings()  # Validate settings on startup
    
    logger.info("Starting AI Chatbot Backend API...")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Available tools: {len(get_tool_info())}")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "AI Chatbot Backend API",
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    _: bool = Depends(verify_api_key)
):
    """Handle chat requests with tool calling and memory.
    
    Args:
        request: Chat request with message and session ID
        
    Returns:
        Chat response with assistant reply and tool usage info
    """
    try:
        # Get or create session
        session_info = memory.get_session_info(request.session_id)
        if not session_info:
            memory.create_session(request.session_id)
            logger.info(f"Created new session: {request.session_id}")
        
        # Get chat history
        chat_history = memory.get_messages(request.session_id)
        
        # Save user message
        memory.add_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        
        # Get agent with optional overrides
        agent = get_agent(
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Execute agent
        result = agent.run(
            user_input=request.message,
            chat_history=chat_history
        )
        
        # Save assistant response
        memory.add_message(
            session_id=request.session_id,
            role="assistant",
            content=result["output"],
            metadata={"tools_used": result["tools_used"]}
        )
        
        return ChatResponse(
            response=result["output"],
            session_id=request.session_id,
            tools_used=result["tools_used"]
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(
    request: ChatRequest,
    _: bool = Depends(verify_api_key)
):
    """Stream chat responses using Server-Sent Events (SSE).
    
    Args:
        request: Chat request with message and session ID
        
    Returns:
        StreamingResponse with SSE formatted chunks
    """
    try:
        # Get or create session
        session_info = memory.get_session_info(request.session_id)
        if not session_info:
            memory.create_session(request.session_id)
        
        # Get chat history
        chat_history = memory.get_messages(request.session_id)
        
        # Save user message
        memory.add_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        
        # Get agent
        agent = get_agent(
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Collect full response for saving
        full_response = ""
        
        async def generate():
            nonlocal full_response
            async for chunk in agent.astream(
                user_input=request.message,
                chat_history=chat_history
            ):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            
            # Save assistant response after streaming completes
            memory.add_message(
                session_id=request.session_id,
                role="assistant",
                content=full_response
            )
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")


@app.post("/sessions", response_model=SessionResponse, tags=["Sessions"])
async def create_session(
    request: SessionCreate,
    _: bool = Depends(verify_api_key)
):
    """Create a new conversation session.
    
    Args:
        request: Session creation request
        
    Returns:
        Session information
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        created = memory.create_session(session_id, request.metadata)
        
        session_info = memory.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return SessionResponse(
            session_id=session_info["session_id"],
            created_at=datetime.fromisoformat(session_info["created_at"].replace(" ", "T")),
            message_count=session_info["message_count"],
            metadata=session_info["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session creation error: {str(e)}")


@app.get("/sessions", response_model=SessionListResponse, tags=["Sessions"])
async def list_sessions(
    limit: int = 100,
    offset: int = 0,
    _: bool = Depends(verify_api_key)
):
    """List all conversation sessions.
    
    Args:
        limit: Maximum number of sessions to return
        offset: Offset for pagination
        
    Returns:
        List of sessions
    """
    try:
        sessions = memory.list_sessions(limit=limit, offset=offset)
        
        session_responses = [
            SessionResponse(
                session_id=s["session_id"],
                created_at=datetime.fromisoformat(s["created_at"].replace(" ", "T")),
                message_count=s["message_count"],
                metadata=s["metadata"]
            )
            for s in sessions
        ]
        
        return SessionListResponse(
            sessions=session_responses,
            total=len(session_responses)
        )
        
    except Exception as e:
        logger.error(f"Session listing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session listing error: {str(e)}")


@app.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def get_session(
    session_id: str,
    _: bool = Depends(verify_api_key)
):
    """Get session information.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session information
    """
    try:
        session_info = memory.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session_info["session_id"],
            created_at=datetime.fromisoformat(session_info["created_at"].replace(" ", "T")),
            message_count=session_info["message_count"],
            metadata=session_info["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session retrieval error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session retrieval error: {str(e)}")


@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(
    session_id: str,
    _: bool = Depends(verify_api_key)
):
    """Delete a conversation session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    try:
        deleted = memory.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": f"Session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session deletion error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session deletion error: {str(e)}")


@app.get("/tools", response_model=ToolsResponse, tags=["Tools"])
async def list_tools(_: bool = Depends(verify_api_key)):
    """List all available tools.
    
    Returns:
        List of available tools with descriptions
    """
    try:
        tools = get_tool_info()
        return ToolsResponse(tools=tools, count=len(tools))
        
    except Exception as e:
        logger.error(f"Tools listing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tools listing error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
