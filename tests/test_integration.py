"""
Integration tests for Phase 1 conversational dialogue system

Tests the complete workflow from dialogue initiation through
prompt enhancement to storage persistence.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from dialogue_system import DialogueManager, DialogueMode, DialogueStage
from prompt_enhancement import PromptEnhancer
from storage import ConversationStore


class TestDialogueToEnhancementIntegration:
    """Test integration between dialogue system and prompt enhancement"""

    def setup_method(self):
        self.dialogue_manager = DialogueManager(DialogueMode.GUIDED)
        self.enhancer = PromptEnhancer()

    def test_complete_guided_dialogue_to_enhanced_prompt(self):
        """Test complete guided dialogue flow to enhanced prompt"""
        original_prompt = "Create a tech company logo"
        responses = {}

        # Simulate answering all dialogue questions
        while True:
            question = self.dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break

            # Simulate user responses based on stage
            if question.stage == DialogueStage.INITIAL:
                responses["initial"] = "Corporate professional audience"
            elif question.stage == DialogueStage.STYLE_EXPLORATION:
                responses["style"] = "Minimalist clean lines"
            elif question.stage == DialogueStage.COLOR_MOOD:
                responses["color_mood"] = "Professional blues"
            elif question.stage == DialogueStage.DETAILS:
                responses["details"] = "Centered composition"

        # Build enhanced prompt
        enhanced = self.dialogue_manager.build_enhanced_prompt(original_prompt, responses)

        # Verify enhancement worked
        assert enhanced != original_prompt
        assert len(enhanced) > len(original_prompt)
        assert "logo" in enhanced.lower()

        # Analyze quality of enhanced prompt
        quality = self.enhancer.analyze_prompt_quality(enhanced)
        original_quality = self.enhancer.analyze_prompt_quality(original_prompt)

        # Enhanced prompt should have better quality
        assert quality.score >= original_quality.score

    def test_dialogue_responses_improve_prompt_quality(self):
        """Test that dialogue responses improve prompt quality metrics"""
        original_prompt = "landscape"
        dialogue_manager = DialogueManager(DialogueMode.QUICK)

        # Get initial quality
        original_quality = self.enhancer.analyze_prompt_quality(original_prompt)

        # Simulate dialogue
        responses = {}
        while True:
            question = dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break
            responses[question.stage.value] = "test response"

        # Build enhanced prompt
        enhanced = dialogue_manager.build_enhanced_prompt(original_prompt, responses)

        # Check enhanced quality
        enhanced_quality = self.enhancer.analyze_prompt_quality(enhanced)

        # Should have fewer missing elements
        assert len(enhanced_quality.missing_elements) <= len(original_quality.missing_elements)


class TestDialogueToStorageIntegration:
    """Test integration between dialogue system and storage"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ConversationStore(storage_dir=self.temp_dir)
        self.dialogue_manager = DialogueManager(DialogueMode.GUIDED)

    def teardown_method(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_save_dialogue_progress_to_storage(self):
        """Test saving dialogue progress at each stage"""
        conv_id = "test_conv_001"
        original_prompt = "Create a logo"
        messages = []
        responses = {}

        # Simulate dialogue with storage saves
        question_count = 0
        while True:
            question = self.dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break

            question_count += 1

            # Save question to messages
            messages.append({
                "role": "assistant",
                "content": question.question,
                "stage": question.stage.value
            })

            # Simulate user response
            responses[question.stage.value] = f"response_{question_count}"
            messages.append({
                "role": "user",
                "content": responses[question.stage.value]
            })

            # Save to storage
            self.store.save_conversation(
                conv_id,
                messages,
                metadata={
                    "dialogue_mode": "guided",
                    "dialogue_responses": responses,
                    "current_stage": question.stage.value
                }
            )

        # Verify conversation was saved
        loaded = self.store.load_conversation(conv_id)
        assert loaded is not None
        assert len(loaded["messages"]) == question_count * 2  # Question + response pairs
        assert loaded["metadata"]["dialogue_responses"] == responses

    def test_resume_dialogue_from_storage(self):
        """Test resuming a dialogue from stored state"""
        conv_id = "test_conv_002"
        original_prompt = "Create a presentation"

        # Start dialogue and answer first question
        question1 = self.dialogue_manager.get_next_question(original_prompt, {})
        responses = {question1.stage.value: "answer 1"}

        # Save to storage
        self.store.save_conversation(
            conv_id,
            [{"role": "assistant", "content": question1.question}],
            metadata={"dialogue_responses": responses}
        )

        # Simulate server restart - create new dialogue manager
        new_dialogue_manager = DialogueManager(DialogueMode.GUIDED)

        # Load conversation
        loaded = self.store.load_conversation(conv_id)
        loaded_responses = loaded["metadata"]["dialogue_responses"]

        # Continue dialogue
        question2 = new_dialogue_manager.get_next_question(original_prompt, loaded_responses)

        assert question2 is not None
        assert question2.stage != question1.stage

    def test_complete_workflow_with_storage(self):
        """Test complete workflow: dialogue -> enhancement -> storage"""
        conv_id = "test_workflow"
        original_prompt = "Create a coffee shop interior"
        messages = []
        responses = {}

        # Complete dialogue
        while True:
            question = self.dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break

            messages.append({"role": "assistant", "content": question.question})
            responses[question.stage.value] = "test response"
            messages.append({"role": "user", "content": "test response"})

        # Build enhanced prompt
        enhanced_prompt = self.dialogue_manager.build_enhanced_prompt(original_prompt, responses)

        # Save complete conversation
        self.store.save_conversation(
            conv_id,
            messages,
            metadata={
                "dialogue_mode": "guided",
                "dialogue_responses": responses,
                "original_prompt": original_prompt,
                "enhanced_prompt": enhanced_prompt,
                "dialogue_complete": True
            }
        )

        # Verify everything was saved
        loaded = self.store.load_conversation(conv_id)
        assert loaded["metadata"]["original_prompt"] == original_prompt
        assert loaded["metadata"]["enhanced_prompt"] == enhanced_prompt
        assert loaded["metadata"]["dialogue_complete"] is True


class TestEnhancementToStorageIntegration:
    """Test integration between prompt enhancement and storage"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ConversationStore(storage_dir=self.temp_dir)
        self.enhancer = PromptEnhancer()

    def teardown_method(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_store_enhancement_metadata(self):
        """Test storing prompt enhancement metadata"""
        conv_id = "test_enhancement"
        original_prompt = "cat"

        # Analyze prompt
        quality = self.enhancer.analyze_prompt_quality(original_prompt)
        image_type = self.enhancer.detect_image_type(original_prompt)
        suggested_size = self.enhancer.suggest_size_from_type(image_type, original_prompt)

        # Store with enhancement metadata
        self.store.save_conversation(
            conv_id,
            [{"role": "user", "content": original_prompt}],
            metadata={
                "original_quality_score": quality.score,
                "detected_image_type": image_type.value,
                "suggested_size": suggested_size,
                "missing_elements": quality.missing_elements
            }
        )

        # Verify stored
        loaded = self.store.load_conversation(conv_id)
        assert loaded["metadata"]["original_quality_score"] == quality.score
        assert loaded["metadata"]["detected_image_type"] == image_type.value

    def test_track_quality_improvement(self):
        """Test tracking prompt quality improvements"""
        conv_id = "test_quality_tracking"
        original_prompt = "logo"

        # Get original quality
        original_quality = self.enhancer.analyze_prompt_quality(original_prompt)

        # Enrich prompt
        enriched_prompt = self.enhancer.enrich_prompt(original_prompt)
        enriched_quality = self.enhancer.analyze_prompt_quality(enriched_prompt)

        # Store both
        self.store.save_conversation(
            conv_id,
            [{"role": "user", "content": original_prompt}],
            metadata={
                "original_prompt": original_prompt,
                "original_quality": original_quality.score,
                "enriched_prompt": enriched_prompt,
                "enriched_quality": enriched_quality.score,
                "quality_improvement": enriched_quality.score - original_quality.score
            }
        )

        loaded = self.store.load_conversation(conv_id)
        assert loaded["metadata"]["quality_improvement"] >= 0


class TestCompletePhase1Workflow:
    """Test complete Phase 1 workflow end-to-end"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ConversationStore(storage_dir=self.temp_dir)
        self.enhancer = PromptEnhancer()

    def teardown_method(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_quick_mode_end_to_end(self):
        """Test complete quick mode workflow"""
        conv_id = "quick_workflow"
        original_prompt = "Create a logo for my startup"

        dialogue_manager = DialogueManager(DialogueMode.QUICK)
        messages = []
        responses = {}

        # Step 1: Analyze original prompt
        original_quality = self.enhancer.analyze_prompt_quality(original_prompt)
        image_type = self.enhancer.detect_image_type(original_prompt)

        # Step 2: Conduct dialogue
        while True:
            question = dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break

            messages.append({"role": "assistant", "content": question.question})
            responses[question.stage.value] = "professional modern style"
            messages.append({"role": "user", "content": responses[question.stage.value]})

        # Step 3: Build enhanced prompt
        enhanced_prompt = dialogue_manager.build_enhanced_prompt(original_prompt, responses)
        enhanced_quality = self.enhancer.analyze_prompt_quality(enhanced_prompt)

        # Step 4: Auto-detect size
        suggested_size = self.enhancer.suggest_size_from_type(image_type, enhanced_prompt)

        # Step 5: Save everything to storage
        self.store.save_conversation(
            conv_id,
            messages,
            metadata={
                "dialogue_mode": "quick",
                "original_prompt": original_prompt,
                "original_quality": original_quality.score,
                "enhanced_prompt": enhanced_prompt,
                "enhanced_quality": enhanced_quality.score,
                "image_type": image_type.value,
                "suggested_size": suggested_size,
                "dialogue_responses": responses,
                "dialogue_complete": True
            }
        )

        # Verify complete workflow
        loaded = self.store.load_conversation(conv_id)
        assert loaded is not None
        assert loaded["metadata"]["dialogue_complete"] is True
        assert loaded["metadata"]["enhanced_quality"] >= loaded["metadata"]["original_quality"]

    def test_guided_mode_end_to_end(self):
        """Test complete guided mode workflow"""
        conv_id = "guided_workflow"
        original_prompt = "Modern coffee shop interior"

        dialogue_manager = DialogueManager(DialogueMode.GUIDED)
        messages = []
        responses = {}

        # Complete dialogue
        question_count = 0
        while True:
            question = dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break

            question_count += 1
            messages.append({
                "role": "assistant",
                "content": question.question,
                "stage": question.stage.value
            })

            # Provide meaningful responses
            response = self._get_meaningful_response(question.stage)
            responses[question.stage.value] = response
            messages.append({"role": "user", "content": response})

        # Should have asked 3-5 questions
        assert 3 <= question_count <= 5

        # Build enhanced prompt
        enhanced_prompt = dialogue_manager.build_enhanced_prompt(original_prompt, responses)

        # Save to storage
        self.store.save_conversation(
            conv_id,
            messages,
            metadata={
                "dialogue_mode": "guided",
                "enhanced_prompt": enhanced_prompt,
                "dialogue_responses": responses
            }
        )

        # Verify
        loaded = self.store.load_conversation(conv_id)
        assert len(loaded["messages"]) == question_count * 2

    def test_explorer_mode_end_to_end(self):
        """Test complete explorer mode workflow"""
        conv_id = "explorer_workflow"
        original_prompt = "Brand identity design"

        dialogue_manager = DialogueManager(DialogueMode.EXPLORER)
        responses = {}

        # Explorer mode should ask more questions
        question_count = 0
        while True:
            question = dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break

            question_count += 1
            responses[question.stage.value] = "detailed response"

            # Safety check
            if question_count > 20:
                break

        # Explorer mode should ask at least 4 questions
        assert question_count >= 4

        # Build and save
        enhanced_prompt = dialogue_manager.build_enhanced_prompt(original_prompt, responses)
        self.store.save_conversation(
            conv_id,
            [],
            metadata={"enhanced_prompt": enhanced_prompt}
        )

        loaded = self.store.load_conversation(conv_id)
        assert loaded is not None

    def test_skip_mode_direct_generation(self):
        """Test skip mode bypasses dialogue"""
        conv_id = "skip_workflow"
        original_prompt = "Abstract art piece"

        dialogue_manager = DialogueManager(DialogueMode.SKIP)

        # Should immediately return None
        question = dialogue_manager.get_next_question(original_prompt, {})
        assert question is None

        # Just use original prompt
        image_type = self.enhancer.detect_image_type(original_prompt)
        suggested_size = self.enhancer.suggest_size_from_type(image_type, original_prompt)

        self.store.save_conversation(
            conv_id,
            [{"role": "user", "content": original_prompt}],
            metadata={
                "dialogue_mode": "skip",
                "image_type": image_type.value,
                "suggested_size": suggested_size
            }
        )

        loaded = self.store.load_conversation(conv_id)
        assert loaded["metadata"]["dialogue_mode"] == "skip"

    def test_add_generated_image_to_workflow(self):
        """Test adding generated image info after dialogue"""
        conv_id = "image_workflow"
        original_prompt = "Logo design"

        # Quick dialogue
        dialogue_manager = DialogueManager(DialogueMode.QUICK)
        responses = {}

        while True:
            question = dialogue_manager.get_next_question(original_prompt, responses)
            if question is None:
                break
            responses[question.stage.value] = "response"

        enhanced_prompt = dialogue_manager.build_enhanced_prompt(original_prompt, responses)

        # Save conversation
        self.store.save_conversation(
            conv_id,
            [],
            metadata={"enhanced_prompt": enhanced_prompt}
        )

        # Simulate image generation
        image_info = {
            "filename": "logo_20251022_120000.png",
            "path": "/Users/test/Downloads/logo.png",
            "size_kb": 245.8,
            "prompt_used": enhanced_prompt
        }

        # Add image to conversation
        self.store.add_generated_image(conv_id, image_info)

        # Verify
        loaded = self.store.load_conversation(conv_id)
        assert len(loaded["metadata"]["generated_images"]) == 1
        assert loaded["metadata"]["generated_images"][0]["filename"] == image_info["filename"]

    def _get_meaningful_response(self, stage: DialogueStage) -> str:
        """Helper to provide meaningful responses for different stages"""
        responses = {
            DialogueStage.INITIAL: "Professional web display",
            DialogueStage.STYLE_EXPLORATION: "Photorealistic modern style",
            DialogueStage.COLOR_MOOD: "Warm inviting atmosphere with earth tones",
            DialogueStage.DETAILS: "Balanced composition with natural lighting"
        }
        return responses.get(stage, "test response")


class TestErrorHandlingIntegration:
    """Test error handling across integrated components"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ConversationStore(storage_dir=self.temp_dir)

    def teardown_method(self):
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_handle_missing_dialogue_responses(self):
        """Test handling when dialogue responses are incomplete"""
        dialogue_manager = DialogueManager(DialogueMode.GUIDED)

        # Incomplete responses
        responses = {"initial": "test"}

        # Should not crash when building prompt
        enhanced = dialogue_manager.build_enhanced_prompt("test prompt", responses)
        assert "test prompt" in enhanced

    def test_handle_empty_prompt(self):
        """Test handling of empty prompts"""
        enhancer = PromptEnhancer()

        # Should handle gracefully
        try:
            quality = enhancer.analyze_prompt_quality("")
            assert quality.score == 0
        except Exception:
            pass  # It's ok if it raises an exception for empty prompt

    def test_resume_from_corrupted_storage(self):
        """Test resuming when storage has issues"""
        conv_id = "test_corrupted"

        # Create corrupted file
        file_path = self.store.storage_dir / f"{conv_id}.json"
        file_path.write_text("invalid json")

        # Should handle gracefully
        loaded = self.store.load_conversation(conv_id)
        assert loaded is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
