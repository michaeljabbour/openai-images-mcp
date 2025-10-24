"""
Prompt Enhancement Engine

Analyzes and improves image generation prompts for better results.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum


class PromptQualityScore(BaseModel):
    """Quality assessment of a prompt"""
    score: int  # 0-100
    missing_elements: List[str]
    suggestions: List[str]
    has_subject: bool
    has_style: bool
    has_mood: bool
    has_colors: bool
    has_composition: bool


class ImageType(str, Enum):
    """Detected image type from prompt"""
    LOGO = "logo"
    PRESENTATION = "presentation"
    SOCIAL_MEDIA = "social_media"
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    PRODUCT = "product"
    ABSTRACT = "abstract"
    ILLUSTRATION = "illustration"
    GENERAL = "general"


class PromptEnhancer:
    """
    Analyzes prompt quality and enriches prompts with best practices.
    """

    # Keywords for detecting image types (order matters - more specific first)
    IMAGE_TYPE_KEYWORDS = {
        ImageType.SOCIAL_MEDIA: ["instagram", "facebook", "twitter", "social media", "social post"],
        ImageType.ABSTRACT: ["abstract art", "abstract geometric", "abstract painting", "abstract"],
        ImageType.PRESENTATION: ["presentation", "slide", "deck", "powerpoint"],
        ImageType.LOGO: ["logo", "brand", "icon", "emblem", "mark"],
        ImageType.PORTRAIT: ["portrait", "headshot", "person", "face", "selfie"],
        ImageType.LANDSCAPE: ["landscape", "scenery", "vista", "horizon"],
        ImageType.PRODUCT: ["product", "merchandise", "item", "commercial"],
        ImageType.ILLUSTRATION: ["illustration", "drawing", "artwork", "sketch"]
    }

    # Quality criteria to check
    QUALITY_CRITERIA = [
        "subject_clarity",
        "style_keywords",
        "mood_descriptors",
        "color_palette",
        "composition_details"
    ]

    def __init__(self):
        self.style_keywords = {
            "photorealistic", "artistic", "painterly", "minimalist", "abstract",
            "cinematic", "dramatic", "professional", "modern", "vintage",
            "contemporary", "traditional", "futuristic", "rustic"
        }

        self.mood_keywords = {
            "calm", "peaceful", "energetic", "dramatic", "mysterious",
            "cheerful", "moody", "bright", "dark", "warm", "cool",
            "inviting", "bold", "subtle", "intense", "serene"
        }

        self.color_keywords = {
            "red", "blue", "green", "yellow", "purple", "orange", "pink",
            "warm", "cool", "vibrant", "muted", "pastel", "neon",
            "monochrome", "colorful", "black", "white", "gray"
        }

        self.composition_keywords = {
            "centered", "rule of thirds", "close-up", "wide angle",
            "symmetrical", "asymmetrical", "balanced", "dynamic",
            "foreground", "background", "depth of field"
        }

    def detect_image_type(self, prompt: str) -> ImageType:
        """Detect what type of image the user wants"""
        prompt_lower = prompt.lower()

        for image_type, keywords in self.IMAGE_TYPE_KEYWORDS.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return image_type

        return ImageType.GENERAL

    def analyze_prompt_quality(self, prompt: str) -> PromptQualityScore:
        """
        Analyze prompt and return quality assessment.

        Checks for: subject, style, mood, colors, composition.
        """
        prompt_lower = prompt.lower()

        # Check for each quality criterion
        has_subject = len(prompt.split()) >= 3  # At least 3 words likely has subject
        has_style = any(keyword in prompt_lower for keyword in self.style_keywords)
        has_mood = any(keyword in prompt_lower for keyword in self.mood_keywords)
        has_colors = any(keyword in prompt_lower for keyword in self.color_keywords)
        has_composition = any(keyword in prompt_lower for keyword in self.composition_keywords)

        # Calculate score
        criteria_met = sum([
            has_subject,
            has_style,
            has_mood,
            has_colors,
            has_composition
        ])
        score = int((criteria_met / len(self.QUALITY_CRITERIA)) * 100)

        # Identify missing elements
        missing = []
        if not has_style:
            missing.append("style_keywords")
        if not has_mood:
            missing.append("mood_descriptors")
        if not has_colors:
            missing.append("color_palette")
        if not has_composition:
            missing.append("composition_details")

        # Generate suggestions
        suggestions = []
        if not has_style:
            suggestions.append("Consider adding visual style (photorealistic, artistic, minimalist)")
        if not has_mood:
            suggestions.append("Specify the mood or atmosphere (dramatic, peaceful, energetic)")
        if not has_colors:
            suggestions.append("Add color preferences (warm tones, vibrant colors, monochrome)")
        if not has_composition:
            suggestions.append("Describe composition (centered, rule of thirds, close-up)")

        return PromptQualityScore(
            score=score,
            missing_elements=missing,
            suggestions=suggestions,
            has_subject=has_subject,
            has_style=has_style,
            has_mood=has_mood,
            has_colors=has_colors,
            has_composition=has_composition
        )

    def enrich_from_dialogue(
        self,
        original_prompt: str,
        dialogue_responses: Dict[str, Any]
    ) -> str:
        """
        Build enhanced prompt from dialogue responses.

        Combines original prompt with information from conversation.
        """
        # This delegates to DialogueManager's build_enhanced_prompt
        # But we can add additional enrichment here

        # Detect image type for optimization
        image_type = self.detect_image_type(original_prompt)

        # Get base enhanced prompt from dialogue
        from dialogue_system import DialogueManager, DialogueMode
        manager = DialogueManager(DialogueMode.GUIDED)
        enhanced = manager.build_enhanced_prompt(original_prompt, dialogue_responses)

        # Add type-specific optimizations
        enhanced = self._add_type_optimizations(enhanced, image_type)

        return enhanced

    def _add_type_optimizations(self, prompt: str, image_type: ImageType) -> str:
        """Add optimizations based on detected image type"""

        if image_type == ImageType.LOGO:
            # Logos need to be clean, scalable, and simple
            if "clean" not in prompt.lower():
                prompt += ", clean design"
            if "scalable" not in prompt.lower():
                prompt += ", scalable"
            if "professional" not in prompt.lower():
                prompt += ", professional"

        elif image_type == ImageType.PRESENTATION:
            # Presentations need high contrast and clarity
            if "high contrast" not in prompt.lower():
                prompt += ", high contrast"
            if "clear" not in prompt.lower():
                prompt += ", clear composition"

        elif image_type == ImageType.SOCIAL_MEDIA:
            # Social media needs eye-catching visuals
            if "eye-catching" not in prompt.lower() and "attention" not in prompt.lower():
                prompt += ", eye-catching"
            if "vibrant" not in prompt.lower() and "bold" not in prompt.lower():
                prompt += ", engaging visual"

        elif image_type == ImageType.PRODUCT:
            # Product photos need professional lighting
            if "professional" not in prompt.lower():
                prompt += ", professional product photography"
            if "lighting" not in prompt.lower():
                prompt += ", studio lighting"

        return prompt

    def suggest_size_from_type(self, image_type: ImageType, prompt: str) -> str:
        """Suggest optimal image size based on type"""

        prompt_lower = prompt.lower()

        # Check for explicit size hints in prompt (highest priority)
        if "story" in prompt_lower or "stories" in prompt_lower:
            return "1024x1536"  # Vertical for stories
        elif "portrait" in prompt_lower or "vertical" in prompt_lower:
            return "1024x1536"
        elif "landscape" in prompt_lower or "wide" in prompt_lower or "horizontal" in prompt_lower:
            return "1536x1024"

        # Use type-based defaults
        if image_type == ImageType.LOGO:
            return "1024x1024"  # Square for logos
        elif image_type == ImageType.PRESENTATION:
            return "1536x1024"  # Landscape for slides
        elif image_type == ImageType.SOCIAL_MEDIA:
            # Check platform
            if "instagram" in prompt_lower:
                return "1024x1024"  # Square for Instagram
            else:
                return "1024x1024"  # Default square
        elif image_type == ImageType.PORTRAIT:
            return "1024x1536"  # Vertical for portraits
        elif image_type == ImageType.LANDSCAPE:
            return "1536x1024"  # Horizontal for landscapes

        # Default square
        return "1024x1024"

    def get_contextual_suggestions(
        self,
        prompt: str,
        image_type: ImageType
    ) -> List[str]:
        """Get specific suggestions based on image type"""

        suggestions = []

        if image_type == ImageType.LOGO:
            suggestions.extend([
                "Consider: What does your brand represent?",
                "Logo tip: Simpler designs are more memorable and scalable",
                "Think about: How will it look in black and white?"
            ])

        elif image_type == ImageType.PRESENTATION:
            suggestions.extend([
                "Presentation tip: Leave space for text overlay",
                "Consider: High contrast works better on projectors",
                "Think about: Landscape orientation (1536x1024) works best"
            ])

        elif image_type == ImageType.SOCIAL_MEDIA:
            suggestions.extend([
                "Social media tip: Bold colors grab attention in feeds",
                "Consider: Mobile viewers see smaller images",
                "Think about: Platform requirements (Instagram 1:1, Stories 9:16)"
            ])

        elif image_type == ImageType.PRODUCT:
            suggestions.extend([
                "Product photo tip: Clean background highlights the product",
                "Consider: Professional lighting shows quality",
                "Think about: Multiple angles for e-commerce"
            ])

        elif image_type == ImageType.PORTRAIT:
            suggestions.extend([
                "Portrait tip: Vertical orientation (1024x1536) works best",
                "Consider: Lighting direction affects mood",
                "Think about: Background should complement, not distract"
            ])

        return suggestions

    def enrich_prompt(
        self,
        original_prompt: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enrich a prompt with best practices.

        This is a simpler version that doesn't require dialogue responses.
        Adds quality keywords automatically.
        """
        image_type = self.detect_image_type(original_prompt)
        quality = self.analyze_prompt_quality(original_prompt)

        enhanced_parts = [original_prompt]

        # Add quality improvements if score is low
        if quality.score < 60:
            # Add style if missing
            if not quality.has_style:
                if image_type == ImageType.LOGO:
                    enhanced_parts.append("modern professional design")
                elif image_type in [ImageType.PRODUCT, ImageType.PRESENTATION]:
                    enhanced_parts.append("photorealistic professional quality")
                else:
                    enhanced_parts.append("high quality professional aesthetic")

            # Add composition if missing
            if not quality.has_composition:
                enhanced_parts.append("well-composed balanced framing")

            # Add lighting/atmosphere if nothing about mood
            if not quality.has_mood:
                enhanced_parts.append("professional lighting")

        # Add type-specific optimizations
        enhanced = ", ".join(enhanced_parts)
        enhanced = self._add_type_optimizations(enhanced, image_type)

        # Add context if provided
        if additional_context:
            if "use_case" in additional_context:
                use_case = additional_context["use_case"]
                if "web" in use_case.lower():
                    enhanced += ", optimized for web display"
                elif "print" in use_case.lower():
                    enhanced += ", high resolution suitable for print"

        return enhanced
