#!/usr/bin/env python3

import asyncio
import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re

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

    def clear_memory(self):
        """Clear all conversation data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM conversations")
            conn.execute("DELETE FROM memory_summaries")
            conn.commit()

class MemoryManager:
    def __init__(self):
        self.db = MemoryDatabase()
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def store_conversation(self, user_message: str, assistant_response: str, importance: float = 1.0) -> str:
        """Store a conversation exchange"""
        # Extract important information for profile
        await self._extract_profile_info(user_message)

        # Store conversation
        conv_id = self.db.store_conversation(
            user_message, assistant_response, self.current_session, importance
        )

        return f"Stored conversation #{conv_id} successfully"

    async def get_context(self, current_message: str, context_limit: int = 5) -> str:
        """Get relevant context for current message"""
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
        if len(current_message) > 10:  # Only search for meaningful messages
            relevant = self.db.search_conversations(current_message, limit=2)
            if relevant:
                context_parts.append("Conversaciones relevantes anteriores:")
                for conv in relevant:
                    context_parts.append(f"Usuario: {conv['user']}")
                    context_parts.append(f"Asistente: {conv['assistant']}")

        context = "\n".join(context_parts)
        if context:
            context += f"\n\nUsuario actual: {current_message}\n\nResponde al usuario actual teniendo en cuenta toda la información anterior:"
        else:
            context = current_message

        return context

    async def search_memory(self, query: str, limit: int = 5) -> str:
        """Search conversation memory"""
        results = self.db.search_conversations(query, limit)

        if not results:
            return "No conversations found"

        search_results = []
        for conv in results:
            search_results.append(f"[{conv['timestamp']}] Usuario: {conv['user']}")
            search_results.append(f"Asistente: {conv['assistant']}")
            search_results.append("---")

        return "\n".join(search_results)

    async def update_profile(self, key: str, value: str) -> str:
        """Update user profile"""
        self.db.update_user_profile(key, value)
        return f"Updated profile: {key} = {value}"

    async def get_profile(self) -> str:
        """Get user profile"""
        profile = self.db.get_user_profile()

        if not profile:
            return "No profile information stored"

        return json.dumps(profile, indent=2, ensure_ascii=False)

    async def clear_memory(self) -> str:
        """Clear conversation memory"""
        self.db.clear_memory()
        return "Memory cleared successfully"

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

        for info_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, msg_lower)
                if match:
                    value = match.group(1)
                    self.db.update_user_profile(info_type, value)
                    break