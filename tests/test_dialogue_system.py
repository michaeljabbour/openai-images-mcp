"""
Unit tests for dialogue_system.py

Tests the conversational dialogue system including dialogue modes,
stage progression, question generation, and prompt enhancement.
"""

import pytest
from dialogue_system import (
    DialogueManager,
    DialogueMode,
    DialogueStage,
    DialogueQuestion
)


class TestDialogueMode:
    """Test DialogueMode enum"""

    def test_dialogue_mode_values(self):
        """Test that all dialogue modes exist"""
        assert DialogueMode.QUICK == "quick"
        assert DialogueMode.GUIDED == "guided"
        assert DialogueMode.EXPLORER == "explorer"
        assert DialogueMode.SKIP == "skip"


class TestDialogueStage:
    """Test DialogueStage enum"""

    def test_dialogue_stage_values(self):
        """Test that all dialogue stages exist"""
        assert DialogueStage.INITIAL == "initial"
        assert DialogueStage.STYLE_EXPLORATION == "style"
        assert DialogueStage.COLOR_MOOD == "color_mood"
        assert DialogueStage.DETAILS == "details"
        assert DialogueStage.READY == "ready"


class TestDialogueManager:
    """Test DialogueManager class"""

    def test_init_quick_mode(self):
        """Test initialization with QUICK mode"""
        manager = DialogueManager(DialogueMode.QUICK)
        assert manager.mode == DialogueMode.QUICK
        assert manager.current_stage == DialogueStage.INITIAL

    def test_init_guided_mode(self):
        """Test initialization with GUIDED mode"""
        manager = DialogueManager(DialogueMode.GUIDED)
        assert manager.mode == DialogueMode.GUIDED
        assert manager.current_stage == DialogueStage.INITIAL

    def test_init_explorer_mode(self):
        """Test initialization with EXPLORER mode"""
        manager = DialogueManager(DialogueMode.EXPLORER)
        assert manager.mode == DialogueMode.EXPLORER
        assert manager.current_stage == DialogueStage.INITIAL

    def test_skip_mode_returns_no_questions(self):
        """Test that SKIP mode returns no questions"""
        manager = DialogueManager(DialogueMode.SKIP)
        question = manager.get_next_question("Create a logo", {})
        assert question is None

    def test_quick_mode_minimal_questions(self):
        """Test that QUICK mode asks minimal questions (1-2)"""
        manager = DialogueManager(DialogueMode.QUICK)

        # First question
        q1 = manager.get_next_question("Create a logo", {})
        assert q1 is not None
        assert q1.stage == DialogueStage.INITIAL

        # Second question
        q2 = manager.get_next_question("Create a logo", {"initial": "test"})
        assert q2 is not None
        assert q2.stage == DialogueStage.STYLE_EXPLORATION

        # Should be done after 2 questions
        q3 = manager.get_next_question(
            "Create a logo",
            {"initial": "test", "style": "modern"}
        )
        assert q3 is None
        assert manager.current_stage == DialogueStage.READY

    def test_guided_mode_balanced_questions(self):
        """Test that GUIDED mode asks 3-5 questions"""
        manager = DialogueManager(DialogueMode.GUIDED)

        questions_asked = []
        responses = {}

        # Ask questions until dialogue complete
        while True:
            question = manager.get_next_question("Create a logo", responses)
            if question is None:
                break
            questions_asked.append(question.stage)
            responses[question.stage.value] = "test response"

        # Guided mode should ask 4 questions (INITIAL, STYLE, COLOR_MOOD, DETAILS)
        assert len(questions_asked) >= 3
        assert len(questions_asked) <= 5
        assert manager.current_stage == DialogueStage.READY

    def test_explorer_mode_comprehensive_questions(self):
        """Test that EXPLORER mode asks comprehensive questions"""
        manager = DialogueManager(DialogueMode.EXPLORER)

        questions_asked = []
        responses = {}

        # Ask questions until dialogue complete
        while True:
            question = manager.get_next_question("Create a logo", responses)
            if question is None:
                break
            questions_asked.append(question.stage)
            responses[question.stage.value] = "test response"

        # Explorer mode should ask at least 4 questions
        assert len(questions_asked) >= 4
        assert manager.current_stage == DialogueStage.READY

    def test_question_structure(self):
        """Test that questions have proper structure"""
        manager = DialogueManager(DialogueMode.GUIDED)
        question = manager.get_next_question("Create a logo", {})

        assert question is not None
        assert hasattr(question, 'stage')
        assert hasattr(question, 'question')
        assert isinstance(question.question, str)
        assert len(question.question) > 0

    def test_logo_detection(self):
        """Test that logo prompts get logo-specific questions"""
        manager = DialogueManager(DialogueMode.GUIDED)
        question = manager.get_next_question("Create a logo for my tech startup", {})

        assert question is not None
        assert "logo" in question.question.lower() or "brand" in question.question.lower()

    def test_presentation_detection(self):
        """Test that presentation prompts get presentation-specific questions"""
        manager = DialogueManager(DialogueMode.GUIDED)
        question = manager.get_next_question("Create a presentation slide", {})

        assert question is not None
        assert "presentation" in question.question.lower() or "audience" in question.question.lower()

    def test_social_media_detection(self):
        """Test that social media prompts get social-specific questions"""
        manager = DialogueManager(DialogueMode.GUIDED)
        question = manager.get_next_question("Create an Instagram post", {})

        assert question is not None
        assert "social" in question.question.lower() or "post" in question.question.lower()

    def test_build_enhanced_prompt_basic(self):
        """Test building enhanced prompt from responses"""
        manager = DialogueManager(DialogueMode.GUIDED)

        original_prompt = "Create a coffee shop"
        responses = {
            "style": "Photorealistic",
            "mood": "Warm and inviting",
            "colors": "Warm browns"
        }

        enhanced = manager.build_enhanced_prompt(original_prompt, responses)

        assert original_prompt in enhanced
        assert len(enhanced) > len(original_prompt)
        # Should contain elements from responses
        assert "photorealistic" in enhanced.lower() or "warm" in enhanced.lower()

    def test_build_enhanced_prompt_with_composition(self):
        """Test enhanced prompt includes composition details"""
        manager = DialogueManager(DialogueMode.GUIDED)

        responses = {
            "composition": "Rule of thirds composition"
        }

        enhanced = manager.build_enhanced_prompt("A landscape", responses)

        assert "rule of thirds" in enhanced.lower() or "composition" in enhanced.lower()

    def test_build_enhanced_prompt_with_colors(self):
        """Test enhanced prompt includes color information"""
        manager = DialogueManager(DialogueMode.GUIDED)

        responses = {
            "colors": "Vibrant saturated colors"
        }

        enhanced = manager.build_enhanced_prompt("Abstract art", responses)

        assert "vibrant" in enhanced.lower() or "saturated" in enhanced.lower()

    def test_stage_progress_tracking(self):
        """Test that stage progress is tracked correctly"""
        manager = DialogueManager(DialogueMode.GUIDED)

        # Initial progress
        progress = manager.get_stage_progress()
        assert progress["current_stage"] == DialogueStage.INITIAL.value
        assert progress["completed_stages"] == 0
        assert progress["total_stages"] > 0
        assert progress["progress_percent"] == 0

        # After one question
        manager.get_next_question("Create a logo", {})
        progress = manager.get_stage_progress()
        assert progress["completed_stages"] == 0  # Still on first stage

        # After completing first stage
        manager.get_next_question("Create a logo", {"initial": "test"})
        progress = manager.get_stage_progress()
        assert progress["completed_stages"] >= 1

    def test_dialogue_with_empty_responses(self):
        """Test that dialogue handles empty responses gracefully"""
        manager = DialogueManager(DialogueMode.GUIDED)

        responses = {
            "style": "",
            "mood": "",
            "colors": ""
        }

        # Should not crash
        enhanced = manager.build_enhanced_prompt("Test prompt", responses)
        assert "Test prompt" in enhanced

    def test_question_has_context(self):
        """Test that questions include helpful context"""
        manager = DialogueManager(DialogueMode.GUIDED)
        question = manager.get_next_question("Create a logo", {})

        # Initial questions should have context
        if question.context:
            assert isinstance(question.context, str)
            assert len(question.context) > 0

    def test_question_has_options_when_appropriate(self):
        """Test that some questions provide options"""
        manager = DialogueManager(DialogueMode.GUIDED)

        questions_with_options = 0
        responses = {}

        while True:
            question = manager.get_next_question("Create a logo", responses)
            if question is None:
                break

            if question.options and len(question.options) > 0:
                questions_with_options += 1

            responses[question.stage.value] = "test"

        # At least some questions should have options
        assert questions_with_options > 0

    def test_stage_sequence_is_logical(self):
        """Test that dialogue stages progress logically"""
        manager = DialogueManager(DialogueMode.GUIDED)

        previous_stage = None
        responses = {}

        while True:
            question = manager.get_next_question("Create a logo", responses)
            if question is None:
                break

            # Stages should progress forward
            if previous_stage:
                # Each stage should be different from previous
                assert question.stage != previous_stage

            previous_stage = question.stage
            responses[question.stage.value] = "test"

    def test_handles_unknown_image_type(self):
        """Test handling of prompts that don't match known types"""
        manager = DialogueManager(DialogueMode.GUIDED)

        # Generic prompt that doesn't match logo/presentation/social
        question = manager.get_next_question("Create something interesting", {})

        assert question is not None
        # Should still get a question, just a generic one
        assert isinstance(question.question, str)


class TestDialogueQuestion:
    """Test DialogueQuestion model"""

    def test_dialogue_question_creation(self):
        """Test creating a DialogueQuestion"""
        question = DialogueQuestion(
            stage=DialogueStage.INITIAL,
            question="What style do you want?",
            options=["Modern", "Classic", "Abstract"],
            context="Style affects the overall look"
        )

        assert question.stage == DialogueStage.INITIAL
        assert question.question == "What style do you want?"
        assert len(question.options) == 3
        assert question.context == "Style affects the overall look"

    def test_dialogue_question_without_options(self):
        """Test creating a question without options"""
        question = DialogueQuestion(
            stage=DialogueStage.DETAILS,
            question="Any specific details to include?"
        )

        assert question.stage == DialogueStage.DETAILS
        assert question.options is None
        assert question.context is None


# Integration-style tests for dialogue flow
class TestDialogueFlow:
    """Test complete dialogue flows"""

    def test_complete_quick_dialogue_flow(self):
        """Test a complete QUICK mode dialogue from start to finish"""
        manager = DialogueManager(DialogueMode.QUICK)
        responses = {}
        prompt = "Create a tech company logo"

        # Simulate complete dialogue with meaningful responses
        question_count = 0
        while True:
            question = manager.get_next_question(prompt, responses)
            if question is None:
                break

            question_count += 1
            # Simulate user response with meaningful content
            if question.stage == DialogueStage.INITIAL:
                responses[question.stage.value] = "Professional corporate audience"
            elif question.stage == DialogueStage.STYLE_EXPLORATION:
                responses[question.stage.value] = "Minimalist modern style"
            else:
                responses[question.stage.value] = f"response_{question_count}"

            # Safety check to prevent infinite loop
            assert question_count < 10, "Too many questions for QUICK mode"

        # Build final prompt
        enhanced = manager.build_enhanced_prompt(prompt, responses)

        assert question_count >= 1
        assert question_count <= 2
        # Enhanced should be different when meaningful responses provided
        assert enhanced != prompt or len(responses) == 0  # Allow same if no responses
        assert len(enhanced) >= len(prompt)

    def test_complete_guided_dialogue_flow(self):
        """Test a complete GUIDED mode dialogue from start to finish"""
        manager = DialogueManager(DialogueMode.GUIDED)
        responses = {}
        prompt = "Create a cozy coffee shop interior"

        question_count = 0
        while True:
            question = manager.get_next_question(prompt, responses)
            if question is None:
                break

            question_count += 1
            responses[question.stage.value] = f"response_{question_count}"

            assert question_count < 20, "Too many questions for GUIDED mode"

        enhanced = manager.build_enhanced_prompt(prompt, responses)

        assert question_count >= 3
        assert question_count <= 5
        assert enhanced != prompt

    def test_dialogue_preserves_original_intent(self):
        """Test that enhanced prompts preserve original intent"""
        manager = DialogueManager(DialogueMode.GUIDED)

        test_cases = [
            "Create a mountain landscape",
            "Design a minimalist logo",
            "Generate an abstract painting"
        ]

        for original_prompt in test_cases:
            responses = {"style": "modern", "mood": "calm"}
            enhanced = manager.build_enhanced_prompt(original_prompt, responses)

            # Original prompt should still be present or its key concepts
            # For "mountain landscape", should preserve "mountain" or "landscape"
            original_words = original_prompt.lower().split()
            key_words = [w for w in original_words if len(w) > 4]

            matches = sum(1 for word in key_words if word in enhanced.lower())
            assert matches > 0, f"Enhanced prompt lost original intent: {original_prompt}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
