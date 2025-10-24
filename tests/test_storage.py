"""
Unit tests for storage.py

Tests the local JSON conversation storage system including
save, load, list, delete, and search operations.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from storage import ConversationStore, get_conversation_store


class TestConversationStore:
    """Test ConversationStore class"""

    def setup_method(self):
        """Set up test fixtures with temporary directory"""
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.store = ConversationStore(storage_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory after tests"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_init_creates_directory(self):
        """Test that initialization creates storage directory"""
        assert self.store.storage_dir.exists()
        assert self.store.storage_dir.is_dir()

    def test_init_with_custom_directory(self):
        """Test initialization with custom storage directory"""
        custom_dir = tempfile.mkdtemp()
        try:
            store = ConversationStore(storage_dir=custom_dir)
            assert store.storage_dir == Path(custom_dir)
            assert store.storage_dir.exists()
        finally:
            shutil.rmtree(custom_dir)

    def test_save_conversation_basic(self):
        """Test basic conversation saving"""
        conv_id = "test_conv_001"
        messages = [
            {"role": "user", "content": "Create a logo"},
            {"role": "assistant", "content": "I'll help create a logo"}
        ]

        self.store.save_conversation(conv_id, messages)

        # Check file was created
        file_path = self.store.storage_dir / f"{conv_id}.json"
        assert file_path.exists()

        # Check file content
        with open(file_path, 'r') as f:
            data = json.load(f)

        assert data["conversation_id"] == conv_id
        assert data["messages"] == messages
        assert "created_at" in data
        assert "updated_at" in data

    def test_save_conversation_with_metadata(self):
        """Test saving conversation with metadata"""
        conv_id = "test_conv_002"
        messages = [{"role": "user", "content": "test"}]
        metadata = {
            "dialogue_mode": "guided",
            "enhanced_prompt": "enhanced test prompt",
            "generated_images": []
        }

        self.store.save_conversation(conv_id, messages, metadata)

        # Load and verify
        loaded = self.store.load_conversation(conv_id)
        assert loaded["metadata"] == metadata

    def test_load_conversation_basic(self):
        """Test loading a saved conversation"""
        conv_id = "test_conv_003"
        messages = [{"role": "user", "content": "test message"}]

        self.store.save_conversation(conv_id, messages)
        loaded = self.store.load_conversation(conv_id)

        assert loaded is not None
        assert loaded["conversation_id"] == conv_id
        assert loaded["messages"] == messages

    def test_load_nonexistent_conversation(self):
        """Test loading a conversation that doesn't exist"""
        loaded = self.store.load_conversation("nonexistent_conv")
        assert loaded is None

    def test_conversation_exists(self):
        """Test checking if conversation exists"""
        conv_id = "test_conv_004"

        assert not self.store.conversation_exists(conv_id)

        self.store.save_conversation(conv_id, [])

        assert self.store.conversation_exists(conv_id)

    def test_list_conversations_empty(self):
        """Test listing conversations when none exist"""
        conversations = self.store.list_conversations()
        assert isinstance(conversations, list)
        assert len(conversations) == 0

    def test_list_conversations_multiple(self):
        """Test listing multiple conversations"""
        # Create multiple conversations
        for i in range(5):
            conv_id = f"test_conv_{i:03d}"
            self.store.save_conversation(conv_id, [{"role": "user", "content": f"test {i}"}])

        conversations = self.store.list_conversations()
        assert len(conversations) == 5

    def test_list_conversations_with_limit(self):
        """Test listing conversations with limit"""
        # Create 10 conversations
        for i in range(10):
            self.store.save_conversation(f"conv_{i}", [])

        # Request only 5
        conversations = self.store.list_conversations(limit=5)
        assert len(conversations) == 5

    def test_list_conversations_most_recent_first(self):
        """Test that conversations are listed most recent first"""
        import time

        # Create conversations with small delays
        conv_ids = []
        for i in range(3):
            conv_id = f"conv_{i}"
            conv_ids.append(conv_id)
            self.store.save_conversation(conv_id, [])
            time.sleep(0.1)  # Small delay to ensure different timestamps

        listed = self.store.list_conversations()

        # Most recent should be last one created
        assert listed[0] == conv_ids[-1]

    def test_get_recent_conversations(self):
        """Test getting recent conversations with summaries"""
        # Create test conversations
        for i in range(3):
            conv_id = f"test_conv_{i}"
            messages = [{"role": "user", "content": f"Prompt {i}"}]
            metadata = {"dialogue_mode": "guided"}
            self.store.save_conversation(conv_id, messages, metadata)

        recent = self.store.get_recent_conversations(limit=10)

        assert len(recent) == 3
        for summary in recent:
            assert "conversation_id" in summary
            assert "message_count" in summary
            assert "first_prompt" in summary
            assert "dialogue_mode" in summary

    def test_delete_conversation(self):
        """Test deleting a conversation"""
        conv_id = "test_conv_delete"
        self.store.save_conversation(conv_id, [])

        assert self.store.conversation_exists(conv_id)

        result = self.store.delete_conversation(conv_id)

        assert result is True
        assert not self.store.conversation_exists(conv_id)

    def test_delete_nonexistent_conversation(self):
        """Test deleting a conversation that doesn't exist"""
        result = self.store.delete_conversation("nonexistent")
        assert result is False

    def test_update_metadata(self):
        """Test updating conversation metadata"""
        conv_id = "test_conv_meta"
        messages = [{"role": "user", "content": "test"}]
        metadata = {"key1": "value1"}

        self.store.save_conversation(conv_id, messages, metadata)

        # Update metadata
        updates = {"key2": "value2"}
        result = self.store.update_metadata(conv_id, updates)

        assert result is True

        # Verify both old and new metadata exist
        loaded = self.store.load_conversation(conv_id)
        assert loaded["metadata"]["key1"] == "value1"
        assert loaded["metadata"]["key2"] == "value2"

    def test_update_metadata_overwrites(self):
        """Test that updating metadata overwrites existing keys"""
        conv_id = "test_conv_meta2"
        self.store.save_conversation(conv_id, [], {"key1": "original"})

        self.store.update_metadata(conv_id, {"key1": "updated"})

        loaded = self.store.load_conversation(conv_id)
        assert loaded["metadata"]["key1"] == "updated"

    def test_add_generated_image(self):
        """Test adding generated image info"""
        conv_id = "test_conv_image"
        self.store.save_conversation(conv_id, [])

        image_info = {
            "filename": "test_image.png",
            "path": "/path/to/image.png",
            "timestamp": "20251022_120000"
        }

        result = self.store.add_generated_image(conv_id, image_info)

        assert result is True

        loaded = self.store.load_conversation(conv_id)
        assert "generated_images" in loaded["metadata"]
        assert len(loaded["metadata"]["generated_images"]) == 1
        assert loaded["metadata"]["generated_images"][0] == image_info

    def test_add_multiple_generated_images(self):
        """Test adding multiple images to a conversation"""
        conv_id = "test_conv_images"
        self.store.save_conversation(conv_id, [])

        # Add multiple images
        for i in range(3):
            image_info = {"filename": f"image_{i}.png"}
            self.store.add_generated_image(conv_id, image_info)

        loaded = self.store.load_conversation(conv_id)
        assert len(loaded["metadata"]["generated_images"]) == 3

    def test_search_conversations_basic(self):
        """Test basic conversation search"""
        # Create conversations with searchable content
        self.store.save_conversation(
            "conv_1",
            [{"role": "user", "content": "Create a logo for tech startup"}]
        )
        self.store.save_conversation(
            "conv_2",
            [{"role": "user", "content": "Generate landscape image"}]
        )

        # Search for "logo"
        results = self.store.search_conversations("logo")

        assert len(results) == 1
        assert results[0]["conversation_id"] == "conv_1"

    def test_search_conversations_case_insensitive(self):
        """Test that search is case-insensitive"""
        self.store.save_conversation(
            "conv_1",
            [{"role": "user", "content": "Create a LOGO"}]
        )

        results = self.store.search_conversations("logo")
        assert len(results) == 1

    def test_search_conversations_with_limit(self):
        """Test search with result limit"""
        # Create multiple matching conversations
        for i in range(5):
            self.store.save_conversation(
                f"conv_{i}",
                [{"role": "user", "content": "Create a logo"}]
            )

        results = self.store.search_conversations("logo", limit=3)
        assert len(results) == 3

    def test_search_conversations_no_matches(self):
        """Test search with no matches"""
        self.store.save_conversation(
            "conv_1",
            [{"role": "user", "content": "Create a logo"}]
        )

        results = self.store.search_conversations("unicorn")
        assert len(results) == 0

    def test_get_storage_stats(self):
        """Test getting storage statistics"""
        # Create some conversations
        for i in range(3):
            self.store.save_conversation(f"conv_{i}", [{"content": "test"}])

        stats = self.store.get_storage_stats()

        assert "total_conversations" in stats
        assert "total_size_bytes" in stats
        assert "total_size_mb" in stats
        assert "storage_directory" in stats

        assert stats["total_conversations"] == 3
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] >= 0

    def test_caching_mechanism(self):
        """Test that conversations are cached in memory"""
        conv_id = "test_cache"
        messages = [{"role": "user", "content": "test"}]

        self.store.save_conversation(conv_id, messages)

        # First load - from disk
        loaded1 = self.store.load_conversation(conv_id)

        # Second load - should be from cache
        loaded2 = self.store.load_conversation(conv_id)

        assert loaded1 == loaded2
        assert conv_id in self.store._cache

    def test_save_updates_cache(self):
        """Test that saving updates the cache"""
        conv_id = "test_cache_update"

        # Save conversation
        self.store.save_conversation(conv_id, [{"content": "first"}])
        assert conv_id in self.store._cache

        # Update conversation
        self.store.save_conversation(conv_id, [{"content": "second"}])

        # Cache should be updated
        cached = self.store._cache[conv_id]
        assert cached["messages"][0]["content"] == "second"

    def test_delete_removes_from_cache(self):
        """Test that deletion removes from cache"""
        conv_id = "test_cache_delete"

        self.store.save_conversation(conv_id, [])
        assert conv_id in self.store._cache

        self.store.delete_conversation(conv_id)
        assert conv_id not in self.store._cache

    def test_timestamps_updated_on_save(self):
        """Test that updated_at timestamp changes on save"""
        import time

        conv_id = "test_timestamps"

        # Initial save
        self.store.save_conversation(conv_id, [{"content": "first"}])
        loaded1 = self.store.load_conversation(conv_id)
        updated_at_1 = loaded1["updated_at"]

        time.sleep(0.1)

        # Update
        self.store.save_conversation(conv_id, [{"content": "second"}])
        loaded2 = self.store.load_conversation(conv_id)
        updated_at_2 = loaded2["updated_at"]

        # updated_at should have changed
        assert updated_at_2 > updated_at_1

    def test_conversation_json_structure(self):
        """Test that saved JSON has correct structure"""
        conv_id = "test_structure"
        messages = [{"role": "user", "content": "test"}]
        metadata = {"key": "value"}

        self.store.save_conversation(conv_id, messages, metadata)

        # Read raw JSON
        file_path = self.store.storage_dir / f"{conv_id}.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Verify structure
        required_fields = ["conversation_id", "created_at", "updated_at", "messages", "metadata"]
        for field in required_fields:
            assert field in data

        assert data["conversation_id"] == conv_id
        assert data["messages"] == messages
        assert data["metadata"] == metadata

    def test_handles_special_characters_in_content(self):
        """Test handling of special characters in message content"""
        conv_id = "test_special"
        messages = [
            {"role": "user", "content": "Test with emoji 🎨 and \"quotes\""},
            {"role": "assistant", "content": "Response with newlines\nand\ttabs"}
        ]

        self.store.save_conversation(conv_id, messages)
        loaded = self.store.load_conversation(conv_id)

        assert loaded["messages"] == messages

    def test_handles_large_conversations(self):
        """Test handling of conversations with many messages"""
        conv_id = "test_large"
        messages = [{"role": "user", "content": f"Message {i}"} for i in range(100)]

        self.store.save_conversation(conv_id, messages)
        loaded = self.store.load_conversation(conv_id)

        assert len(loaded["messages"]) == 100

    def test_preserves_message_order(self):
        """Test that message order is preserved"""
        conv_id = "test_order"
        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"}
        ]

        self.store.save_conversation(conv_id, messages)
        loaded = self.store.load_conversation(conv_id)

        for i, msg in enumerate(loaded["messages"]):
            assert msg["content"] == messages[i]["content"]


class TestGetConversationStore:
    """Test the global conversation store singleton"""

    def test_get_conversation_store_creates_instance(self):
        """Test that get_conversation_store returns an instance"""
        store = get_conversation_store()
        assert store is not None
        assert isinstance(store, ConversationStore)

    def test_get_conversation_store_returns_same_instance(self):
        """Test that get_conversation_store returns the same instance"""
        store1 = get_conversation_store()
        store2 = get_conversation_store()
        assert store1 is store2


class TestEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ConversationStore(storage_dir=self.temp_dir)

    def teardown_method(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_empty_messages_list(self):
        """Test saving conversation with empty messages"""
        conv_id = "test_empty"
        self.store.save_conversation(conv_id, [])

        loaded = self.store.load_conversation(conv_id)
        assert loaded["messages"] == []

    def test_none_metadata(self):
        """Test saving with None metadata"""
        conv_id = "test_none_meta"
        self.store.save_conversation(conv_id, [], metadata=None)

        loaded = self.store.load_conversation(conv_id)
        assert "metadata" in loaded
        assert loaded["metadata"] == {}

    def test_update_metadata_nonexistent_conversation(self):
        """Test updating metadata for nonexistent conversation"""
        result = self.store.update_metadata("nonexistent", {"key": "value"})
        assert result is False

    def test_add_image_to_nonexistent_conversation(self):
        """Test adding image to nonexistent conversation"""
        result = self.store.add_generated_image("nonexistent", {"image": "data"})
        assert result is False

    def test_corrupted_json_file(self):
        """Test handling of corrupted JSON files"""
        conv_id = "test_corrupted"
        file_path = self.store.storage_dir / f"{conv_id}.json"

        # Create corrupted JSON file
        file_path.write_text("{ invalid json content }")

        # Should return None instead of crashing
        loaded = self.store.load_conversation(conv_id)
        assert loaded is None

    def test_created_at_preserved_on_update(self):
        """Test that created_at timestamp is preserved when updating"""
        conv_id = "test_created_preserved"

        # Initial save
        self.store.save_conversation(conv_id, [{"content": "first"}])
        loaded1 = self.store.load_conversation(conv_id)
        created_at_1 = loaded1["created_at"]

        import time
        time.sleep(0.1)

        # Update with metadata including created_at
        self.store.save_conversation(
            conv_id,
            [{"content": "second"}],
            metadata={"created_at": created_at_1}
        )
        loaded2 = self.store.load_conversation(conv_id)

        # created_at should be preserved
        assert loaded2["created_at"] == created_at_1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
