#!/usr/bin/env python3

import asyncio
import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryDatabase:
    def __init__(self, db_path: str = "data/memory/conversation.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    context_summary TEXT,
                    importance_score REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS memory_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    summary_text TEXT NOT NULL,
                    start_timestamp TEXT,
                    end_timestamp TEXT,
                    conversation_count INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def store_conversation(self, user_msg: str, assistant_msg: str,
                          session_id: str = "default", importance: float = 1.0) -> int:
        """Store a conversation exchange"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations
                (timestamp, session_id, user_message, assistant_response, importance_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                session_id,
                user_msg,
                assistant_msg,
                importance
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recent_conversations(self, limit: int = 10, session_id: str = "default") -> List[Dict]:
        """Get recent conversations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, user_message, assistant_response, importance_score
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (session_id, limit))

            rows = cursor.fetchall()
            return [
                {
                    "timestamp": row[0],
                    "user": row[1],
                    "assistant": row[2],
                    "importance": row[3]
                }
                for row in rows
            ]

    def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """Simple text search in conversations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, user_message, assistant_response, importance_score
                FROM conversations
                WHERE user_message LIKE ? OR assistant_response LIKE ?
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))

            rows = cursor.fetchall()
            return [
                {
                    "timestamp": row[0],
                    "user": row[1],
                    "assistant": row[2],
                    "importance": row[3]
                }
                for row in rows
            ]

    def update_user_profile(self, key: str, value: str):
        """Update user profile information"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO user_profile (key, value, last_updated)
                VALUES (?, ?, ?)
            ''', (key, value, datetime.now().isoformat()))
            conn.commit()

    def get_user_profile(self) -> Dict[str, str]:
        """Get user profile information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM user_profile')
            return dict(cursor.fetchall())

class MemoryServer:
    def __init__(self):
        self.server = Server("memory-server")
        self.db = MemoryDatabase()
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Register tools
        self.server.list_tools = self.list_tools
        self.server.call_tool = self.call_tool

    async def list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List available memory tools"""
        tools = [
            Tool(
                name="store_conversation",
                description="Store a conversation exchange in memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_message": {"type": "string"},
                        "assistant_response": {"type": "string"},
                        "importance": {"type": "number", "default": 1.0}
                    },
                    "required": ["user_message", "assistant_response"]
                }
            ),
            Tool(
                name="get_context",
                description="Get relevant conversation context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "current_message": {"type": "string"},
                        "context_limit": {"type": "number", "default": 5}
                    },
                    "required": ["current_message"]
                }
            ),
            Tool(
                name="search_memory",
                description="Search through conversation history",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "number", "default": 5}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="update_profile",
                description="Update user profile information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "value": {"type": "string"}
                    },
                    "required": ["key", "value"]
                }
            ),
            Tool(
                name="get_profile",
                description="Get user profile information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ),
            Tool(
                name="clear_memory",
                description="Clear conversation memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "confirm": {"type": "boolean", "default": False}
                    }
                }
            )
        ]

        return ListToolsResult(tools=tools)

    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls"""
        try:
            if request.name == "store_conversation":
                return await self._store_conversation(request.arguments)
            elif request.name == "get_context":
                return await self._get_context(request.arguments)
            elif request.name == "search_memory":
                return await self._search_memory(request.arguments)
            elif request.name == "update_profile":
                return await self._update_profile(request.arguments)
            elif request.name == "get_profile":
                return await self._get_profile(request.arguments)
            elif request.name == "clear_memory":
                return await self._clear_memory(request.arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )
        except Exception as e:
            logger.error(f"Error in tool call {request.name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )

    async def _store_conversation(self, args: Dict[str, Any]) -> CallToolResult:
        """Store conversation exchange"""
        user_msg = args["user_message"]
        assistant_msg = args["assistant_response"]
        importance = args.get("importance", 1.0)

        # Extract important information for profile
        await self._extract_profile_info(user_msg)

        # Store conversation
        conv_id = self.db.store_conversation(
            user_msg, assistant_msg, self.current_session, importance
        )

        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Stored conversation #{conv_id} successfully"
            )]
        )

    async def _get_context(self, args: Dict[str, Any]) -> CallToolResult:
        """Get relevant context for current message"""
        current_msg = args["current_message"]
        context_limit = args.get("context_limit", 5)

        # Get recent conversations
        recent = self.db.get_recent_conversations(limit=context_limit)

        # Get user profile
        profile = self.db.get_user_profile()

        # Build context
        context_parts = []

        if profile:
            profile_text = ", ".join([f"{k}: {v}" for k, v in profile.items()])
            context_parts.append(f"Información del usuario: {profile_text}")

        if recent:
            context_parts.append("Conversación reciente:")
            for conv in reversed(recent[-3:]):  # Last 3 exchanges
                context_parts.append(f"Usuario: {conv['user']}")
                context_parts.append(f"Asistente: {conv['assistant']}")

        # Search for relevant past conversations
        if len(current_msg) > 10:  # Only search for meaningful messages
            relevant = self.db.search_conversations(current_msg, limit=2)
            if relevant:
                context_parts.append("Conversaciones relevantes anteriores:")
                for conv in relevant:
                    context_parts.append(f"Usuario: {conv['user']}")
                    context_parts.append(f"Asistente: {conv['assistant']}")

        context = "\n".join(context_parts)
        if context:
            context += f"\n\nUsuario actual: {current_msg}\n\nResponde al usuario actual teniendo en cuenta toda la información anterior:"
        else:
            context = current_msg

        return CallToolResult(
            content=[TextContent(type="text", text=context)]
        )

    async def _search_memory(self, args: Dict[str, Any]) -> CallToolResult:
        """Search conversation memory"""
        query = args["query"]
        limit = args.get("limit", 5)

        results = self.db.search_conversations(query, limit)

        if not results:
            return CallToolResult(
                content=[TextContent(type="text", text="No conversations found")]
            )

        search_results = []
        for conv in results:
            search_results.append(f"[{conv['timestamp']}] Usuario: {conv['user']}")
            search_results.append(f"Asistente: {conv['assistant']}")
            search_results.append("---")

        return CallToolResult(
            content=[TextContent(type="text", text="\n".join(search_results))]
        )

    async def _update_profile(self, args: Dict[str, Any]) -> CallToolResult:
        """Update user profile"""
        key = args["key"]
        value = args["value"]

        self.db.update_user_profile(key, value)

        return CallToolResult(
            content=[TextContent(type="text", text=f"Updated profile: {key} = {value}")]
        )

    async def _get_profile(self, args: Dict[str, Any]) -> CallToolResult:
        """Get user profile"""
        profile = self.db.get_user_profile()

        if not profile:
            return CallToolResult(
                content=[TextContent(type="text", text="No profile information stored")]
            )

        profile_text = json.dumps(profile, indent=2, ensure_ascii=False)
        return CallToolResult(
            content=[TextContent(type="text", text=profile_text)]
        )

    async def _clear_memory(self, args: Dict[str, Any]) -> CallToolResult:
        """Clear conversation memory"""
        confirm = args.get("confirm", False)

        if not confirm:
            return CallToolResult(
                content=[TextContent(type="text", text="Memory clear cancelled - confirmation required")]
            )

        # Clear database
        with sqlite3.connect(self.db.db_path) as conn:
            conn.execute("DELETE FROM conversations")
            conn.execute("DELETE FROM memory_summaries")
            conn.commit()

        return CallToolResult(
            content=[TextContent(type="text", text="Memory cleared successfully")]
        )

    async def _extract_profile_info(self, user_message: str):
        """Extract important user information from messages"""
        msg_lower = user_message.lower()

        # Simple pattern matching for common information
        patterns = {
            "name": [r"mi nombre es (\w+)", r"me llamo (\w+)", r"soy (\w+)"],
            "age": [r"tengo (\d+) años", r"mi edad es (\d+)"],
            "profession": [r"soy (\w+)", r"trabajo como (\w+)", r"estudio (\w+)"],
            "location": [r"vivo en (\w+)", r"soy de (\w+)"],
        }

        import re

        for info_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, msg_lower)
                if match:
                    value = match.group(1)
                    self.db.update_user_profile(info_type, value)
                    break

async def main():
    """Run the MCP Memory Server"""
    memory_server = MemoryServer()

    # Run the server
    try:
        logger.info("Starting MCP Memory Server...")
        await memory_server.server.run()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Memory Server...")

if __name__ == "__main__":
    asyncio.run(main())