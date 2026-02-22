"""Persistent memory management for conversation history."""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages persistent conversation memory using SQLite."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize memory storage.
        
        Args:
            db_path: Path to SQLite database file. Defaults to config setting.
        """
        self.db_path = db_path or settings.sqlite_db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            )
        """)
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session 
            ON messages(session_id, timestamp)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new conversation session.
        
        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata
            
        Returns:
            True if session was created, False if it already exists
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            metadata_json = json.dumps(metadata or {})
            cursor.execute("""
                INSERT INTO sessions (session_id, metadata)
                VALUES (?, ?)
            """, (session_id, metadata_json))
            conn.commit()
            logger.info(f"Created session: {session_id}")
            return True
        except sqlite3.IntegrityError:
            logger.debug(f"Session already exists: {session_id}")
            return False
        finally:
            conn.close()
    
    def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to a session.
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Ensure session exists
            self.create_session(session_id)
            
            # Update session timestamp
            cursor.execute("""
                UPDATE sessions 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE session_id = ?
            """, (session_id,))
            
            # Insert message
            metadata_json = json.dumps(metadata or {})
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, metadata_json))
            
            conn.commit()
            logger.debug(f"Added {role} message to session {session_id}")
        finally:
            conn.close()
    
    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to retrieve
            
        Returns:
            List of message dictionaries with role, content, and timestamp
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT role, content, timestamp 
                FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            """
            params = (session_id,)
            
            if limit:
                query += " LIMIT ?"
                params = (session_id, limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            messages = [
                {
                    "role": row[0],
                    "content": row[1],
                    "timestamp": row[2]
                }
                for row in rows
            ]
            
            return messages
        finally:
            conn.close()
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session info dict or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT session_id, created_at, updated_at, metadata,
                       (SELECT COUNT(*) FROM messages WHERE messages.session_id = sessions.session_id) as message_count
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "session_id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "metadata": json.loads(row[3] or "{}"),
                "message_count": row[4]
            }
        finally:
            conn.close()
    
    def list_sessions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all sessions.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Offset for pagination
            
        Returns:
            List of session info dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT session_id, created_at, updated_at, metadata,
                       (SELECT COUNT(*) FROM messages WHERE messages.session_id = sessions.session_id) as message_count
                FROM sessions
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            sessions = [
                {
                    "session_id": row[0],
                    "created_at": row[1],
                    "updated_at": row[2],
                    "metadata": json.loads(row[3] or "{}"),
                    "message_count": row[4]
                }
                for row in rows
            ]
            
            return sessions
        finally:
            conn.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logger.info(f"Deleted session: {session_id}")
            
            return deleted
        finally:
            conn.close()
    
    def clear_old_sessions(self, days: int = 30) -> int:
        """Clear sessions older than specified days.
        
        Args:
            days: Number of days to keep sessions
            
        Returns:
            Number of sessions deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM sessions 
                WHERE updated_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            
            if deleted > 0:
                logger.info(f"Cleared {deleted} old sessions (older than {days} days)")
            
            return deleted
        finally:
            conn.close()


# Global memory instance
memory = ConversationMemory()
