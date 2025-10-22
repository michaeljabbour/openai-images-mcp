"""
Conversational Dialogue System for Image Generation

Implements pre-generation dialogue to help users refine their vision
through natural conversation before generating images.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class DialogueMode(str, Enum):
    """Dialogue depth options for users"""
    QUICK = "quick"        # 1-2 questions, fast path
    GUIDED = "guided"      # 3-5 questions, balanced (default)
    EXPLORER = "explorer"  # Deep exploration, 6+ questions
    SKIP = "skip"          # Direct generation, no dialogue


class DialogueStage(str, Enum):
    """Stages in the conversational flow"""
    INITIAL = "initial"              # First understanding
    STYLE_EXPLORATION = "style"      # Visual style preferences
    COLOR_MOOD = "color_mood"        # Colors and atmosphere
    DETAILS = "details"              # Composition specifics
    READY = "ready"                  # Ready to generate


class DialogueQuestion(BaseModel):
    """A question to ask the user"""
    stage: DialogueStage
    question: str
    options: Optional[List[str]] = None
    context: Optional[str] = None  # Why we're asking this


class DialogueManager:
    """
    Orchestrates conversational dialogue flow based on mode.

    Guides users through questions to build better prompts.
    """

    def __init__(self, mode: DialogueMode):
        self.mode = mode
        self.current_stage = DialogueStage.INITIAL

        # Define question sequences for each mode
        self.question_sequences = {
            DialogueMode.QUICK: [
                DialogueStage.INITIAL,
                DialogueStage.STYLE_EXPLORATION
            ],
            DialogueMode.GUIDED: [
                DialogueStage.INITIAL,
                DialogueStage.STYLE_EXPLORATION,
                DialogueStage.COLOR_MOOD,
                DialogueStage.DETAILS
            ],
            DialogueMode.EXPLORER: [
                DialogueStage.INITIAL,
                DialogueStage.STYLE_EXPLORATION,
                DialogueStage.COLOR_MOOD,
                DialogueStage.DETAILS,
                # Explorer mode asks deeper follow-up questions
            ]
        }

    def get_next_question(
        self,
        original_prompt: str,
        responses: Dict[str, Any]
    ) -> Optional[DialogueQuestion]:
        """
        Get the next question to ask based on current stage and responses.

        Returns None when dialogue is complete.
        """
        if self.mode == DialogueMode.SKIP:
            return None

        # Get question sequence for current mode
        sequence = self.question_sequences.get(self.mode, [])

        # Find next unanswered stage
        answered_stages = set(responses.keys())
        for stage in sequence:
            if stage.value not in answered_stages:
                self.current_stage = stage
                return self._generate_question_for_stage(
                    stage,
                    original_prompt,
                    responses
                )

        # All questions answered
        self.current_stage = DialogueStage.READY
        return None

    def _generate_question_for_stage(
        self,
        stage: DialogueStage,
        original_prompt: str,
        responses: Dict[str, Any]
    ) -> DialogueQuestion:
        """Generate the appropriate question for this stage"""

        if stage == DialogueStage.INITIAL:
            return self._initial_questions(original_prompt)
        elif stage == DialogueStage.STYLE_EXPLORATION:
            return self._style_questions(original_prompt, responses)
        elif stage == DialogueStage.COLOR_MOOD:
            return self._color_mood_questions(original_prompt, responses)
        elif stage == DialogueStage.DETAILS:
            return self._detail_questions(original_prompt, responses)

        return None

    def _initial_questions(self, prompt: str) -> DialogueQuestion:
        """Initial understanding questions"""

        # Detect image type from prompt
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["logo", "brand", "icon"]):
            return DialogueQuestion(
                stage=DialogueStage.INITIAL,
                question="Tell me about what this logo represents. What should it communicate?",
                context="Understanding your brand helps create a logo that resonates"
            )

        elif any(word in prompt_lower for word in ["presentation", "slide", "deck"]):
            return DialogueQuestion(
                stage=DialogueStage.INITIAL,
                question="What's the presentation about? Who's the audience?",
                options=[
                    "Corporate/professional audience",
                    "Academic/educational setting",
                    "Public/general audience"
                ],
                context="Presentation context affects visual style"
            )

        elif any(word in prompt_lower for word in ["social", "instagram", "post", "twitter", "facebook"]):
            return DialogueQuestion(
                stage=DialogueStage.INITIAL,
                question="What's the goal of this social media post?",
                options=[
                    "Eye-catching and shareable",
                    "Professional brand content",
                    "Personal/authentic vibe"
                ],
                context="Social media images need to grab attention quickly"
            )

        else:
            # General image
            return DialogueQuestion(
                stage=DialogueStage.INITIAL,
                question="How will you use this image?",
                options=[
                    "Web/digital display",
                    "Print material",
                    "Personal art/creative project",
                    "Reference/concept exploration"
                ],
                context="Use case helps optimize the image"
            )

    def _style_questions(
        self,
        prompt: str,
        responses: Dict[str, Any]
    ) -> DialogueQuestion:
        """Visual style exploration questions"""

        return DialogueQuestion(
            stage=DialogueStage.STYLE_EXPLORATION,
            question="What visual style appeals to you?",
            options=[
                "Photorealistic (like a photograph)",
                "Artistic/Painterly (expressive, creative)",
                "Minimalist (clean, simple lines)",
                "Detailed/Complex (rich with elements)",
                "Abstract/Conceptual (symbolic, interpretive)"
            ],
            context="Style choice dramatically affects the final image"
        )

    def _color_mood_questions(
        self,
        prompt: str,
        responses: Dict[str, Any]
    ) -> DialogueQuestion:
        """Color palette and mood questions"""

        if self.mode == DialogueMode.QUICK:
            # Quick mode: one combined question
            return DialogueQuestion(
                stage=DialogueStage.COLOR_MOOD,
                question="Any specific colors or mood in mind? (e.g., 'warm sunset tones' or 'professional blues')",
                context="Colors and mood set the emotional tone"
            )
        else:
            # Guided/Explorer: separate questions
            # Check if we already asked about colors
            if "colors" not in responses:
                return DialogueQuestion(
                    stage=DialogueStage.COLOR_MOOD,
                    question="What color palette works best?",
                    options=[
                        "Warm colors (reds, oranges, yellows)",
                        "Cool colors (blues, greens, purples)",
                        "Neutral/Monochrome (blacks, whites, grays)",
                        "Vibrant/Saturated (bold, energetic)",
                        "Muted/Pastel (soft, subtle)",
                        "Specific colors (tell me which)"
                    ],
                    context="Color psychology affects how viewers feel"
                )
            else:
                # Ask about mood separately
                return DialogueQuestion(
                    stage=DialogueStage.COLOR_MOOD,
                    question="What mood or atmosphere should it convey?",
                    options=[
                        "Professional & polished",
                        "Energetic & dynamic",
                        "Calm & peaceful",
                        "Bold & dramatic",
                        "Warm & inviting",
                        "Modern & cutting-edge"
                    ],
                    context="Mood guides lighting and composition choices"
                )

    def _detail_questions(
        self,
        prompt: str,
        responses: Dict[str, Any]
    ) -> DialogueQuestion:
        """Composition detail questions"""

        # Ask about level of detail
        if "detail_level" not in responses:
            return DialogueQuestion(
                stage=DialogueStage.DETAILS,
                question="How detailed should it be?",
                options=[
                    "Highly detailed (rich with elements)",
                    "Balanced (some detail, not overwhelming)",
                    "Minimalist (focus on essentials)"
                ],
                context="Detail level affects visual impact"
            )

        # Ask about composition
        if "composition" not in responses:
            return DialogueQuestion(
                stage=DialogueStage.DETAILS,
                question="Any composition preferences?",
                options=[
                    "Centered subject (traditional, balanced)",
                    "Rule of thirds (dynamic, professional)",
                    "Close-up/Intimate (focus on details)",
                    "Wide view (show context)",
                    "Let you decide (AI optimizes)"
                ],
                context="Composition affects visual flow"
            )

        # If explorer mode, ask about specific elements
        if self.mode == DialogueMode.EXPLORER and "specific_elements" not in responses:
            return DialogueQuestion(
                stage=DialogueStage.DETAILS,
                question="Any specific elements to include or avoid?",
                context="Fine-tuning ensures the image matches your vision"
            )

        return None

    def build_enhanced_prompt(
        self,
        original_prompt: str,
        responses: Dict[str, Any]
    ) -> str:
        """
        Build enhanced prompt from dialogue responses.

        Combines user's original prompt with information gathered
        through conversation.
        """
        parts = [original_prompt]

        # Add style
        if "style" in responses:
            style = responses["style"]
            if "photorealistic" in style.lower():
                parts.append("photorealistic style, high detail, professional photography")
            elif "artistic" in style.lower() or "painterly" in style.lower():
                parts.append("artistic painting style, expressive brushwork")
            elif "minimalist" in style.lower():
                parts.append("minimalist design, clean lines, simple composition")
            elif "detailed" in style.lower() or "complex" in style.lower():
                parts.append("highly detailed, rich with elements")
            elif "abstract" in style.lower():
                parts.append("abstract conceptual style, symbolic interpretation")

        # Add mood
        if "mood" in responses:
            mood = responses["mood"]
            if "professional" in mood.lower():
                parts.append("professional polished aesthetic")
            elif "energetic" in mood.lower():
                parts.append("energetic dynamic atmosphere")
            elif "calm" in mood.lower() or "peaceful" in mood.lower():
                parts.append("calm peaceful serene mood")
            elif "dramatic" in mood.lower():
                parts.append("bold dramatic lighting")
            elif "warm" in mood.lower() or "inviting" in mood.lower():
                parts.append("warm inviting atmosphere")
            elif "modern" in mood.lower():
                parts.append("modern cutting-edge aesthetic")

        # Add color palette
        if "colors" in responses or "color_mood" in responses:
            color_info = responses.get("colors") or responses.get("color_mood", "")
            color_lower = color_info.lower()

            if "warm" in color_lower:
                parts.append("warm color palette with reds, oranges, and yellows")
            elif "cool" in color_lower:
                parts.append("cool color palette with blues, greens, and purples")
            elif "neutral" in color_lower or "monochrome" in color_lower:
                parts.append("neutral monochromatic color scheme")
            elif "vibrant" in color_lower or "saturated" in color_lower:
                parts.append("vibrant saturated colors, bold and energetic")
            elif "muted" in color_lower or "pastel" in color_lower:
                parts.append("muted pastel tones, soft and subtle")
            else:
                # User specified specific colors
                parts.append(f"color palette: {color_info}")

        # Add composition details
        if "composition" in responses:
            comp = responses["composition"]
            if "centered" in comp.lower():
                parts.append("centered composition, balanced framing")
            elif "rule of thirds" in comp.lower():
                parts.append("rule of thirds composition, dynamic placement")
            elif "close-up" in comp.lower() or "intimate" in comp.lower():
                parts.append("close-up intimate view, focus on details")
            elif "wide" in comp.lower():
                parts.append("wide establishing shot, contextual view")

        # Add detail level
        if "detail_level" in responses:
            detail = responses["detail_level"]
            if "highly detailed" in detail.lower():
                parts.append("highly detailed, intricate elements")
            elif "minimalist" in detail.lower():
                parts.append("minimalist approach, focus on essentials")

        # Add specific elements if mentioned
        if "specific_elements" in responses:
            elements = responses["specific_elements"]
            if elements and elements.strip():
                parts.append(f"include: {elements}")

        # Add use case optimizations
        if "initial" in responses:
            use_case = responses["initial"]
            if "web" in use_case.lower() or "digital" in use_case.lower():
                parts.append("optimized for digital display")
            elif "print" in use_case.lower():
                parts.append("high contrast suitable for print")
            elif "social" in use_case.lower():
                parts.append("eye-catching for social media")

        # Combine all parts into coherent prompt
        enhanced = ", ".join(parts)

        # Clean up duplicate commas and spacing
        enhanced = enhanced.replace(",,", ",").strip()

        return enhanced

    def get_stage_progress(self) -> Dict[str, Any]:
        """Get current dialogue progress"""
        sequence = self.question_sequences.get(self.mode, [])
        total_stages = len(sequence)
        current_index = sequence.index(self.current_stage) if self.current_stage in sequence else 0

        return {
            "current_stage": self.current_stage.value,
            "completed_stages": current_index,
            "total_stages": total_stages,
            "progress_percent": int((current_index / total_stages) * 100) if total_stages > 0 else 0
        }
