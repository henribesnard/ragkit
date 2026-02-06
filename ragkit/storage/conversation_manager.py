"""Conversation Manager for RAGKIT Desktop.

Provides a high-level interface for managing conversations and messages,
including export functionality.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragkit.storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message data model."""

    id: str
    conversation_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    sources: list[dict] = field(default_factory=list)
    latency_ms: int | None = None
    token_count: int | None = None
    created_at: str = ""
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            conversation_id=data["conversation_id"],
            role=data["role"],
            content=data["content"],
            sources=data.get("sources", []),
            latency_ms=data.get("latency_ms"),
            token_count=data.get("token_count"),
            created_at=data.get("created_at", ""),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class Conversation:
    """Conversation data model."""

    id: str
    kb_id: str | None
    title: str | None
    created_at: str
    updated_at: str
    metadata: dict = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict, messages: list[Message] | None = None) -> Conversation:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            kb_id=data.get("kb_id"),
            title=data.get("title"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            metadata=data.get("metadata", {}),
            messages=messages or [],
        )

    def to_dict(self, include_messages: bool = True) -> dict:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "kb_id": self.kb_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
        if include_messages:
            result["messages"] = [m.to_dict() for m in self.messages]
        return result


class ConversationManager:
    """High-level manager for conversations and messages.

    Provides CRUD operations and export functionality.
    """

    def __init__(self, db: SQLiteStore) -> None:
        """Initialize conversation manager.

        Args:
            db: SQLite store instance
        """
        self.db = db

    async def create(
        self,
        kb_id: str | None = None,
        title: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            kb_id: Optional knowledge base to link
            title: Optional title
            metadata: Optional metadata

        Returns:
            Created conversation.
        """
        data = self.db.create_conversation(
            kb_id=kb_id,
            title=title,
            metadata=metadata,
        )
        conv = Conversation.from_dict(data)
        logger.info(f"Created conversation: {conv.id}")
        return conv

    async def get(
        self,
        conv_id: str,
        include_messages: bool = True,
    ) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conv_id: Conversation ID
            include_messages: Whether to load messages

        Returns:
            Conversation or None if not found.
        """
        data = self.db.get_conversation(conv_id)
        if not data:
            return None

        messages = []
        if include_messages:
            msg_data = self.db.list_messages(conv_id)
            messages = [Message.from_dict(m) for m in msg_data]

        return Conversation.from_dict(data, messages)

    async def list(
        self,
        kb_id: str | None = None,
        limit: int = 50,
    ) -> list[Conversation]:
        """List conversations.

        Args:
            kb_id: Optional filter by knowledge base
            limit: Maximum number to return

        Returns:
            List of conversations (without messages).
        """
        items = self.db.list_conversations(kb_id=kb_id, limit=limit)
        return [Conversation.from_dict(item) for item in items]

    async def update(
        self,
        conv_id: str,
        title: str | None = None,
        kb_id: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation | None:
        """Update a conversation.

        Args:
            conv_id: Conversation ID
            title: New title
            kb_id: New knowledge base link
            metadata: New metadata

        Returns:
            Updated conversation or None if not found.
        """
        updates = {}
        if title is not None:
            updates["title"] = title
        if kb_id is not None:
            updates["kb_id"] = kb_id
        if metadata is not None:
            updates["metadata"] = metadata

        if not updates:
            return await self.get(conv_id, include_messages=False)

        data = self.db.update_conversation(conv_id, **updates)
        return Conversation.from_dict(data) if data else None

    async def delete(self, conv_id: str) -> bool:
        """Delete a conversation and all its messages.

        Args:
            conv_id: Conversation ID

        Returns:
            True if deleted, False if not found.
        """
        deleted = self.db.delete_conversation(conv_id)
        if deleted:
            logger.info(f"Deleted conversation: {conv_id}")
        return deleted

    # --- Message Operations ---

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[dict] | None = None,
        latency_ms: int | None = None,
        token_count: int | None = None,
        metadata: dict | None = None,
    ) -> Message:
        """Add a message to a conversation.

        Args:
            conversation_id: Parent conversation ID
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            sources: Source citations
            latency_ms: Response latency
            token_count: Token count
            metadata: Additional metadata

        Returns:
            Created message.

        Raises:
            ValueError: If conversation not found.
        """
        # Validate conversation exists
        conv = self.db.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation not found: {conversation_id}")

        data = self.db.create_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            latency_ms=latency_ms,
            token_count=token_count,
            metadata=metadata,
        )

        return Message.from_dict(data)

    async def get_messages(self, conversation_id: str) -> list[Message]:
        """Get all messages in a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages in chronological order.
        """
        items = self.db.list_messages(conversation_id)
        return [Message.from_dict(item) for item in items]

    # --- Auto-titling ---

    async def auto_title(self, conv_id: str) -> str | None:
        """Generate a title from the first user message.

        Args:
            conv_id: Conversation ID

        Returns:
            Generated title or None if no messages.
        """
        messages = await self.get_messages(conv_id)
        user_messages = [m for m in messages if m.role == "user"]

        if not user_messages:
            return None

        # Use first user message, truncated
        first_msg = user_messages[0].content
        title = first_msg[:50]
        if len(first_msg) > 50:
            title = title.rsplit(" ", 1)[0] + "..."

        await self.update(conv_id, title=title)
        return title

    # --- Export Functionality ---

    async def export_json(self, conv_id: str) -> str:
        """Export a conversation to JSON format.

        Args:
            conv_id: Conversation ID

        Returns:
            JSON string.

        Raises:
            ValueError: If conversation not found.
        """
        conv = await self.get(conv_id, include_messages=True)
        if not conv:
            raise ValueError(f"Conversation not found: {conv_id}")

        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
            "conversation": conv.to_dict(include_messages=True),
        }

        return json.dumps(export_data, indent=2, ensure_ascii=False)

    async def export_markdown(self, conv_id: str) -> str:
        """Export a conversation to Markdown format.

        Args:
            conv_id: Conversation ID

        Returns:
            Markdown string.

        Raises:
            ValueError: If conversation not found.
        """
        conv = await self.get(conv_id, include_messages=True)
        if not conv:
            raise ValueError(f"Conversation not found: {conv_id}")

        lines = []

        # Header
        title = conv.title or "Untitled Conversation"
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**Created:** {conv.created_at}")
        lines.append(f"**Updated:** {conv.updated_at}")
        if conv.kb_id:
            lines.append(f"**Knowledge Base:** {conv.kb_id}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Messages
        for msg in conv.messages:
            role_label = {
                "user": "**User**",
                "assistant": "**Assistant**",
                "system": "**System**",
            }.get(msg.role, f"**{msg.role}**")

            lines.append(f"### {role_label}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")

            # Sources
            if msg.sources:
                lines.append("*Sources:*")
                for src in msg.sources:
                    src_name = src.get("source", src.get("filename", "Unknown"))
                    lines.append(f"- {src_name}")
                lines.append("")

            # Metadata
            if msg.latency_ms:
                lines.append(f"*Response time: {msg.latency_ms}ms*")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    async def export_to_file(
        self,
        conv_id: str,
        output_path: Path | str,
        format: str = "json",
    ) -> Path:
        """Export a conversation to a file.

        Args:
            conv_id: Conversation ID
            output_path: Output file path
            format: Export format ('json' or 'markdown')

        Returns:
            Path to created file.

        Raises:
            ValueError: If invalid format or conversation not found.
        """
        output_path = Path(output_path)

        if format == "json":
            content = await self.export_json(conv_id)
            if not output_path.suffix:
                output_path = output_path.with_suffix(".json")
        elif format in ("markdown", "md"):
            content = await self.export_markdown(conv_id)
            if not output_path.suffix:
                output_path = output_path.with_suffix(".md")
        else:
            raise ValueError(f"Unsupported export format: {format}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Exported conversation {conv_id} to {output_path}")
        return output_path

    # --- Utility Methods ---

    async def get_conversation_stats(self, conv_id: str) -> dict:
        """Get statistics for a conversation.

        Args:
            conv_id: Conversation ID

        Returns:
            Statistics dictionary.
        """
        messages = await self.get_messages(conv_id)

        user_count = sum(1 for m in messages if m.role == "user")
        assistant_count = sum(1 for m in messages if m.role == "assistant")
        total_tokens = sum(m.token_count or 0 for m in messages)
        avg_latency = 0

        latencies = [m.latency_ms for m in messages if m.latency_ms]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)

        return {
            "message_count": len(messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "total_tokens": total_tokens,
            "average_latency_ms": round(avg_latency, 2),
        }
