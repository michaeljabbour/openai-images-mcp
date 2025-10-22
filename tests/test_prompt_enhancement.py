"""
Unit tests for prompt_enhancement.py

Tests the prompt quality analysis, image type detection,
size suggestions, and prompt enrichment functionality.
"""

import pytest
from prompt_enhancement import (
    PromptEnhancer,
    PromptQualityScore,
    ImageType
)


class TestImageType:
    """Test ImageType enum"""

    def test_image_type_values(self):
        """Test that all image types exist"""
        assert ImageType.LOGO == "logo"
        assert ImageType.PRESENTATION == "presentation"
        assert ImageType.SOCIAL_MEDIA == "social_media"
        assert ImageType.PORTRAIT == "portrait"
        assert ImageType.LANDSCAPE == "landscape"
        assert ImageType.PRODUCT == "product"
        assert ImageType.ABSTRACT == "abstract"
        assert ImageType.ILLUSTRATION == "illustration"
        assert ImageType.GENERAL == "general"


class TestPromptEnhancer:
    """Test PromptEnhancer class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.enhancer = PromptEnhancer()

    def test_init(self):
        """Test PromptEnhancer initialization"""
        assert self.enhancer is not None
        assert hasattr(self.enhancer, 'style_keywords')
        assert hasattr(self.enhancer, 'mood_keywords')
        assert hasattr(self.enhancer, 'color_keywords')
        assert hasattr(self.enhancer, 'composition_keywords')


class TestImageTypeDetection:
    """Test image type detection"""

    def setup_method(self):
        self.enhancer = PromptEnhancer()

    def test_detect_logo(self):
        """Test logo detection"""
        prompts = [
            "Create a logo for my company",
            "Design a brand icon",
            "Tech startup logo with circuit patterns",
            "Modern emblem for a coffee shop"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.LOGO, f"Failed to detect logo in: {prompt}"

    def test_detect_presentation(self):
        """Test presentation detection"""
        prompts = [
            "Create a presentation slide",
            "Background for PowerPoint deck",
            "Professional slide design"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.PRESENTATION

    def test_detect_social_media(self):
        """Test social media detection"""
        prompts = [
            "Instagram post about coffee",
            "Facebook banner image",
            "Twitter header graphic",
            "Social media post for brand"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.SOCIAL_MEDIA, f"Failed to detect social media in: {prompt}"

    def test_detect_portrait(self):
        """Test portrait detection"""
        prompts = [
            "Portrait of a person",
            "Professional headshot",
            "Face with dramatic lighting",
            "Character portrait"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.PORTRAIT

    def test_detect_landscape(self):
        """Test landscape detection"""
        prompts = [
            "Mountain landscape at sunset",
            "Scenic vista of ocean",
            "Landscape with rolling hills",
            "Beautiful scenery"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.LANDSCAPE

    def test_detect_product(self):
        """Test product detection"""
        prompts = [
            "Product photography of watch",
            "Commercial item showcase",
            "Merchandise on white background"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.PRODUCT

    def test_detect_abstract(self):
        """Test abstract detection"""
        prompts = [
            "Abstract geometric shapes",
            "Abstract art with vibrant colors",
            "Abstract painting with flowing forms"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.ABSTRACT, f"Failed to detect abstract in: {prompt}"

    def test_detect_illustration(self):
        """Test illustration detection"""
        prompts = [
            "Illustration of a dragon",
            "Hand-drawn artwork",
            "Sketch of a building"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.ILLUSTRATION

    def test_detect_general(self):
        """Test general fallback"""
        prompts = [
            "Something interesting",
            "A random image",
            "Test prompt"
        ]
        for prompt in prompts:
            detected = self.enhancer.detect_image_type(prompt)
            assert detected == ImageType.GENERAL


class TestPromptQualityAnalysis:
    """Test prompt quality analysis"""

    def setup_method(self):
        self.enhancer = PromptEnhancer()

    def test_analyze_minimal_prompt(self):
        """Test analysis of minimal prompt"""
        quality = self.enhancer.analyze_prompt_quality("cat")

        assert isinstance(quality, PromptQualityScore)
        assert quality.score < 50  # Minimal prompt should score low
        assert len(quality.missing_elements) > 0
        assert len(quality.suggestions) > 0

    def test_analyze_good_prompt(self):
        """Test analysis of well-crafted prompt"""
        quality = self.enhancer.analyze_prompt_quality(
            "Photorealistic portrait of a person with warm lighting, "
            "professional quality, centered composition, "
            "dramatic mood with vibrant colors"
        )

        assert quality.score >= 80  # Good prompt should score high
        assert quality.has_subject
        assert quality.has_style
        assert quality.has_mood
        assert quality.has_colors
        assert quality.has_composition

    def test_analyze_prompt_with_style(self):
        """Test detection of style keywords"""
        prompts_with_style = [
            "Photorealistic image of a cat",
            "Minimalist design",
            "Artistic painting style",
            "Cinematic lighting"
        ]
        for prompt in prompts_with_style:
            quality = self.enhancer.analyze_prompt_quality(prompt)
            assert quality.has_style

    def test_analyze_prompt_with_mood(self):
        """Test detection of mood keywords"""
        prompts_with_mood = [
            "Calm peaceful scene",
            "Energetic dynamic composition",
            "Dramatic mysterious atmosphere",
            "Cheerful bright image"
        ]
        for prompt in prompts_with_mood:
            quality = self.enhancer.analyze_prompt_quality(prompt)
            assert quality.has_mood

    def test_analyze_prompt_with_colors(self):
        """Test detection of color keywords"""
        prompts_with_colors = [
            "Warm red and orange tones",
            "Cool blue atmosphere",
            "Vibrant colorful scene",
            "Monochrome black and white"
        ]
        for prompt in prompts_with_colors:
            quality = self.enhancer.analyze_prompt_quality(prompt)
            assert quality.has_colors

    def test_analyze_prompt_with_composition(self):
        """Test detection of composition keywords"""
        prompts_with_composition = [
            "Centered subject",
            "Rule of thirds composition",
            "Close-up view",
            "Wide angle perspective"
        ]
        for prompt in prompts_with_composition:
            quality = self.enhancer.analyze_prompt_quality(prompt)
            assert quality.has_composition

    def test_quality_score_range(self):
        """Test that quality scores are in valid range"""
        test_prompts = [
            "cat",
            "A beautiful landscape",
            "Photorealistic portrait with dramatic lighting, warm colors, and centered composition"
        ]
        for prompt in test_prompts:
            quality = self.enhancer.analyze_prompt_quality(prompt)
            assert 0 <= quality.score <= 100

    def test_suggestions_are_actionable(self):
        """Test that suggestions are meaningful"""
        quality = self.enhancer.analyze_prompt_quality("Create a logo")

        for suggestion in quality.suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 10  # Suggestions should be meaningful
            # Suggestions should mention what's missing
            assert any(word in suggestion.lower() for word in ['add', 'consider', 'specify', 'describe'])


class TestSizeSuggestions:
    """Test image size suggestions"""

    def setup_method(self):
        self.enhancer = PromptEnhancer()

    def test_suggest_size_for_logo(self):
        """Test size suggestion for logos"""
        size = self.enhancer.suggest_size_from_type(ImageType.LOGO, "company logo")
        assert size == "1024x1024"  # Logos should be square

    def test_suggest_size_for_presentation(self):
        """Test size suggestion for presentations"""
        size = self.enhancer.suggest_size_from_type(ImageType.PRESENTATION, "slide background")
        assert size == "1536x1024"  # Presentations should be landscape

    def test_suggest_size_for_portrait(self):
        """Test size suggestion for portraits"""
        size = self.enhancer.suggest_size_from_type(ImageType.PORTRAIT, "person portrait")
        assert size == "1024x1536"  # Portraits should be vertical

    def test_suggest_size_for_landscape(self):
        """Test size suggestion for landscapes"""
        size = self.enhancer.suggest_size_from_type(ImageType.LANDSCAPE, "mountain scenery")
        assert size == "1536x1024"  # Landscapes should be horizontal

    def test_suggest_size_with_explicit_portrait_hint(self):
        """Test size detection from prompt keywords"""
        size = self.enhancer.suggest_size_from_type(ImageType.GENERAL, "vertical portrait style image")
        assert size == "1024x1536"

    def test_suggest_size_with_explicit_landscape_hint(self):
        """Test size detection from prompt keywords"""
        size = self.enhancer.suggest_size_from_type(ImageType.GENERAL, "wide landscape format")
        assert size == "1536x1024"

    def test_suggest_size_for_instagram(self):
        """Test size for Instagram posts"""
        size = self.enhancer.suggest_size_from_type(ImageType.SOCIAL_MEDIA, "Instagram post")
        assert size == "1024x1024"  # Instagram default is square

    def test_suggest_size_for_instagram_story(self):
        """Test size for Instagram stories"""
        size = self.enhancer.suggest_size_from_type(ImageType.SOCIAL_MEDIA, "Instagram story")
        assert size == "1024x1536"  # Stories are vertical


class TestPromptEnrichment:
    """Test prompt enrichment functionality"""

    def setup_method(self):
        self.enhancer = PromptEnhancer()

    def test_enrich_minimal_prompt(self):
        """Test enriching a minimal prompt"""
        original = "cat"
        enriched = self.enhancer.enrich_prompt(original)

        assert len(enriched) > len(original)
        assert "cat" in enriched.lower()

    def test_enrich_logo_prompt(self):
        """Test enriching logo prompts with type-specific optimizations"""
        original = "Create a tech company logo"
        enriched = self.enhancer.enrich_prompt(original)

        # Should add logo-specific terms
        assert any(word in enriched.lower() for word in ['professional', 'clean', 'modern'])

    def test_enrich_product_prompt(self):
        """Test enriching product prompts"""
        original = "Product photo of a watch"
        enriched = self.enhancer.enrich_prompt(original)

        # Should add product photography terms
        assert any(word in enriched.lower() for word in ['professional', 'lighting', 'photography'])

    def test_enrich_preserves_original(self):
        """Test that enrichment preserves original prompt"""
        test_prompts = [
            "A mountain landscape",
            "Abstract geometric art",
            "Portrait of a person"
        ]
        for original in test_prompts:
            enriched = self.enhancer.enrich_prompt(original)
            # Original words should still be present
            original_words = original.lower().split()
            for word in original_words:
                if len(word) > 3:  # Skip short words like "a", "of"
                    assert word in enriched.lower()

    def test_enrich_with_context(self):
        """Test enrichment with additional context"""
        original = "Create an image"
        context = {"use_case": "web display"}
        enriched = self.enhancer.enrich_prompt(original, additional_context=context)

        assert "web" in enriched.lower() or "display" in enriched.lower()

    def test_enrich_with_print_context(self):
        """Test enrichment with print context"""
        original = "Create an image"
        context = {"use_case": "print material"}
        enriched = self.enhancer.enrich_prompt(original, additional_context=context)

        assert "print" in enriched.lower() or "resolution" in enriched.lower()


class TestContextualSuggestions:
    """Test contextual suggestions based on image type"""

    def setup_method(self):
        self.enhancer = PromptEnhancer()

    def test_logo_suggestions(self):
        """Test logo-specific suggestions"""
        suggestions = self.enhancer.get_contextual_suggestions(
            "company logo",
            ImageType.LOGO
        )

        assert len(suggestions) > 0
        # Should mention brand, simplicity, or scalability
        combined = " ".join(suggestions).lower()
        assert any(word in combined for word in ['brand', 'simple', 'scalable', 'memorable'])

    def test_presentation_suggestions(self):
        """Test presentation-specific suggestions"""
        suggestions = self.enhancer.get_contextual_suggestions(
            "slide background",
            ImageType.PRESENTATION
        )

        assert len(suggestions) > 0
        combined = " ".join(suggestions).lower()
        assert any(word in combined for word in ['text', 'contrast', 'projector'])

    def test_social_media_suggestions(self):
        """Test social media-specific suggestions"""
        suggestions = self.enhancer.get_contextual_suggestions(
            "Instagram post",
            ImageType.SOCIAL_MEDIA
        )

        assert len(suggestions) > 0
        combined = " ".join(suggestions).lower()
        assert any(word in combined for word in ['attention', 'mobile', 'platform'])

    def test_product_suggestions(self):
        """Test product-specific suggestions"""
        suggestions = self.enhancer.get_contextual_suggestions(
            "product photo",
            ImageType.PRODUCT
        )

        assert len(suggestions) > 0
        combined = " ".join(suggestions).lower()
        assert any(word in combined for word in ['background', 'lighting', 'quality'])

    def test_portrait_suggestions(self):
        """Test portrait-specific suggestions"""
        suggestions = self.enhancer.get_contextual_suggestions(
            "person portrait",
            ImageType.PORTRAIT
        )

        assert len(suggestions) > 0
        combined = " ".join(suggestions).lower()
        assert any(word in combined for word in ['lighting', 'vertical', 'background'])


class TestTypeOptimizations:
    """Test type-specific optimizations"""

    def setup_method(self):
        self.enhancer = PromptEnhancer()

    def test_logo_optimization(self):
        """Test logo-specific optimizations are added"""
        prompt = "Create a logo"
        optimized = self.enhancer._add_type_optimizations(prompt, ImageType.LOGO)

        assert "clean" in optimized.lower() or "scalable" in optimized.lower()

    def test_presentation_optimization(self):
        """Test presentation-specific optimizations"""
        prompt = "Background image"
        optimized = self.enhancer._add_type_optimizations(prompt, ImageType.PRESENTATION)

        assert "contrast" in optimized.lower() or "clear" in optimized.lower()

    def test_social_media_optimization(self):
        """Test social media-specific optimizations"""
        prompt = "Create an image"
        optimized = self.enhancer._add_type_optimizations(prompt, ImageType.SOCIAL_MEDIA)

        assert "eye-catching" in optimized.lower() or "engaging" in optimized.lower()

    def test_product_optimization(self):
        """Test product-specific optimizations"""
        prompt = "Show a watch"
        optimized = self.enhancer._add_type_optimizations(prompt, ImageType.PRODUCT)

        assert "professional" in optimized.lower() and "lighting" in optimized.lower()

    def test_optimization_doesnt_duplicate(self):
        """Test that optimization doesn't add duplicate terms"""
        prompt = "Professional clean modern logo"
        optimized = self.enhancer._add_type_optimizations(prompt, ImageType.LOGO)

        # Should not add "professional" again since it's already there
        professional_count = optimized.lower().count("professional")
        assert professional_count <= 2  # Allow for some duplication but not excessive


# Integration tests
class TestPromptEnhancementIntegration:
    """Integration tests for complete enhancement workflow"""

    def setup_method(self):
        self.enhancer = PromptEnhancer()

    def test_complete_enhancement_workflow(self):
        """Test complete enhancement from analysis to enrichment"""
        original_prompt = "logo"

        # Analyze quality
        quality = self.enhancer.analyze_prompt_quality(original_prompt)
        assert quality.score < 50

        # Detect type
        image_type = self.enhancer.detect_image_type(original_prompt)
        assert image_type == ImageType.LOGO

        # Suggest size
        size = self.enhancer.suggest_size_from_type(image_type, original_prompt)
        assert size == "1024x1024"

        # Enrich prompt
        enriched = self.enhancer.enrich_prompt(original_prompt)
        assert len(enriched) > len(original_prompt)

        # Re-analyze enriched prompt
        enriched_quality = self.enhancer.analyze_prompt_quality(enriched)
        assert enriched_quality.score > quality.score

    def test_enhancement_improves_quality_score(self):
        """Test that enrichment improves quality scores"""
        test_cases = [
            "cat",
            "logo",
            "landscape",
            "portrait"
        ]

        for original in test_cases:
            original_quality = self.enhancer.analyze_prompt_quality(original)
            enriched = self.enhancer.enrich_prompt(original)
            enriched_quality = self.enhancer.analyze_prompt_quality(enriched)

            assert enriched_quality.score >= original_quality.score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
