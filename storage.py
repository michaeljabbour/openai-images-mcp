"""
Local Storage for Conversation Persistence

Stores conversations as JSON files in ~/.openai-images-mcp/
Following MCP best practice for local-first data storage.
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class ConversationStore:
    """
    Manages local storage of conversations.

    Stores conversations as JSON files in user's home directory:
    ~/.openai-images-mcp/conversations/

    No encryption by default (optional for future if user needs it).
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize storage with directory path.

        Args:
            storage_dir: Custom storage directory, or None for default
                        (~/.openai-images-mcp/conversations/)
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir).expanduser()
        else:
            self.storage_dir = Path.home() / ".openai-images-mcp" / "conversations"

        # Create directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for performance
        self._cache: Dict[str, dict] = {}

    def save_conversation(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save conversation to local JSON file.

        Args:
            conversation_id: Unique conversation identifier
            messages: List of conversation messages
            metadata: Optional metadata (dialogue_mode, generated_images, etc.)
        """
        conversation_data = {
            "conversation_id": conversation_id,
            "created_at": metadata.get("created_at") if metadata else datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": messages,
            "metadata": metadata or {}
        }

        # Save to file
        file_path = self._get_file_path(conversation_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)

        # Update cache
        self._cache[conversation_id] = conversation_data

    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conversation from local storage.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Conversation data dict or None if not found
        """
        # Check cache first
        if conversation_id in self._cache:
            return self._cache[conversation_id]

        # Load from file
        file_path = self._get_file_path(conversation_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)

            # Cache it
            self._cache[conversation_id] = conversation_data
            return conversation_data

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading conversation {conversation_id}: {e}")
            return None

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if conversation exists"""
        return self._get_file_path(conversation_id).exists()

    def list_conversations(self, limit: Optional[int] = None) -> List[str]:
        """
        List all conversation IDs, most recent first.

        Args:
            limit: Optional limit on number of conversations to return

        Returns:
            List of conversation IDs
        """
        # Get all JSON files in storage directory
        json_files = list(self.storage_dir.glob("*.json"))

        # Sort by modification time (most recent first)
        json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Extract conversation IDs from filenames
        conversation_ids = [f.stem for f in json_files]

        if limit:
            conversation_ids = conversation_ids[:limit]

        return conversation_ids

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversations with summary information.

        Args:
            limit: Number of conversations to return

        Returns:
            List of conversation summaries
        """
        conv_ids = self.list_conversations(limit=limit)
        summaries = []

        for conv_id in conv_ids:
            conv_data = self.load_conversation(conv_id)
            if conv_data:
                # Extract summary info
                messages = conv_data.get("messages", [])
                first_message = messages[0] if messages else None

                summary = {
                    "conversation_id": conv_id,
                    "updated_at": conv_data.get("updated_at"),
                    "message_count": len(messages),
                    "first_prompt": first_message.get("content") if first_message else None,
                    "dialogue_mode": conv_data.get("metadata", {}).get("dialogue_mode"),
                    "has_images": len(conv_data.get("metadata", {}).get("generated_images", [])) > 0
                }
                summaries.append(summary)

        return summaries

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation from storage.

        User's right to delete their data.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_file_path(conversation_id)

        if not file_path.exists():
            return False

        try:
            file_path.unlink()  # Delete file

            # Remove from cache
            if conversation_id in self._cache:
                del self._cache[conversation_id]

            return True

        except IOError as e:
            print(f"Error deleting conversation {conversation_id}: {e}")
            return False

    def update_metadata(
        self,
        conversation_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update conversation metadata without rewriting entire conversation.

        Args:
            conversation_id: Conversation to update
            metadata_updates: New metadata to merge

        Returns:
            True if updated successfully
        """
        conv_data = self.load_conversation(conversation_id)
        if not conv_data:
            return False

        # Merge metadata
        if "metadata" not in conv_data:
            conv_data["metadata"] = {}

        conv_data["metadata"].update(metadata_updates)
        conv_data["updated_at"] = datetime.now().isoformat()

        # Save updated conversation
        self.save_conversation(
            conversation_id,
            conv_data["messages"],
            conv_data["metadata"]
        )

        return True

    def add_generated_image(
        self,
        conversation_id: str,
        image_info: Dict[str, Any]
    ) -> bool:
        """
        Add generated image information to conversation metadata.

        Args:
            conversation_id: Conversation ID
            image_info: Dict with file_id, path, timestamp, etc.

        Returns:
            True if added successfully
        """
        conv_data = self.load_conversation(conversation_id)
        if not conv_data:
            return False

        # Initialize generated_images list if not present
        if "metadata" not in conv_data:
            conv_data["metadata"] = {}

        if "generated_images" not in conv_data["metadata"]:
            conv_data["metadata"]["generated_images"] = []

        # Add image info
        conv_data["metadata"]["generated_images"].append(image_info)
        conv_data["updated_at"] = datetime.now().isoformat()

        # Save
        self.save_conversation(
            conversation_id,
            conv_data["messages"],
            conv_data["metadata"]
        )

        return True

    def search_conversations(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search conversations by text content.

        Simple text search - for Phase 3 we can add semantic search.

        Args:
            query: Search query string
            limit: Max results to return

        Returns:
            List of matching conversation summaries
        """
        query_lower = query.lower()
        matches = []

        for conv_id in self.list_conversations():
            conv_data = self.load_conversation(conv_id)
            if not conv_data:
                continue

            # Search in messages
            for message in conv_data.get("messages", []):
                content = message.get("content", "")
                if isinstance(content, str) and query_lower in content.lower():
                    # Found match
                    summary = {
                        "conversation_id": conv_id,
                        "updated_at": conv_data.get("updated_at"),
                        "matching_message": content[:100] + "..." if len(content) > 100 else content
                    }
                    matches.append(summary)
                    break  # One match per conversation

            if len(matches) >= limit:
                break

        return matches

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored conversations.

        Returns:
            Dict with stats (total conversations, total size, etc.)
        """
        json_files = list(self.storage_dir.glob("*.json"))

        total_size = sum(f.stat().st_size for f in json_files)
        total_conversations = len(json_files)

        return {
            "total_conversations": total_conversations,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_directory": str(self.storage_dir)
        }

    def _get_file_path(self, conversation_id: str) -> Path:
        """Get file path for a conversation ID"""
        return self.storage_dir / f"{conversation_id}.json"


# Singleton instance for easy access
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """
    Get the global ConversationStore instance.

    Creates it if it doesn't exist yet.
    """
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store
