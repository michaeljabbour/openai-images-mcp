"""
Unit tests for image_verification.py

Tests the image quality verification system that checks
generated images before delivery to users.
"""

import pytest
import tempfile
from pathlib import Path

from image_verification import (
    ImageVerifier,
    ImageVerification,
    get_image_verifier
)


class TestImageVerification:
    """Test ImageVerification model"""

    def test_image_verification_creation(self):
        """Test creating an ImageVerification"""
        verification = ImageVerification(
            passed=True,
            confidence=0.95,
            issues=[],
            suggestions=["Check colors"],
            analysis="Image looks good"
        )

        assert verification.passed is True
        assert verification.confidence == 0.95
        assert len(verification.issues) == 0
        assert len(verification.suggestions) == 1
        assert "good" in verification.analysis.lower()
        assert verification.timestamp is not None

    def test_verification_with_issues(self):
        """Test verification with detected issues"""
        verification = ImageVerification(
            passed=False,
            confidence=0.45,
            issues=["Text not present", "Wrong colors"],
            suggestions=["Add text", "Adjust colors"],
            analysis="Multiple issues detected"
        )

        assert verification.passed is False
        assert verification.confidence < 0.5
        assert len(verification.issues) == 2
        assert "Text not present" in verification.issues


class TestImageVerifier:
    """Test ImageVerifier class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.verifier = ImageVerifier()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up"""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_verifier_initialization(self):
        """Test verifier initializes correctly"""
        assert self.verifier is not None
        assert self.verifier.verification_enabled is True

    def test_verify_nonexistent_image(self):
        """Test verification of non-existent image"""
        verification = self.verifier.verify_image(
            image_path="/nonexistent/image.png",
            original_prompt="Test prompt",
            enhanced_prompt="Enhanced test prompt"
        )

        assert verification.passed is False
        assert len(verification.issues) > 0
        assert "read image" in verification.issues[0].lower()

    def test_verify_with_minimal_params(self):
        """Test verification with minimal parameters"""
        # Create a dummy image file
        image_path = Path(self.temp_dir) / "test_image.png"
        image_path.write_bytes(b"fake image data")

        verification = self.verifier.verify_image(
            image_path=str(image_path),
            original_prompt="A simple logo",
            enhanced_prompt="A simple professional logo"
        )

        # Should pass (Phase 1 always passes)
        assert verification.passed is True
        assert verification.confidence > 0
        assert verification.analysis is not None

    def test_verify_with_dialogue_responses(self):
        """Test verification with dialogue responses"""
        image_path = Path(self.temp_dir) / "test.png"
        image_path.write_bytes(b"test")

        dialogue_responses = {
            "style": "Minimalist",
            "mood": "Professional",
            "colors": "Blue and white"
        }

        verification = self.verifier.verify_image(
            image_path=str(image_path),
            original_prompt="Company logo",
            enhanced_prompt="Professional company logo, minimalist style",
            dialogue_responses=dialogue_responses
        )

        assert verification.passed is True
        # Analysis should mention the requirements
        assert verification.analysis is not None

    def test_verify_with_image_type(self):
        """Test verification with specific image type"""
        image_path = Path(self.temp_dir) / "logo.png"
        image_path.write_bytes(b"test")

        verification = self.verifier.verify_image(
            image_path=str(image_path),
            original_prompt="Tech startup logo",
            enhanced_prompt="Modern tech startup logo",
            image_type="logo"
        )

        assert verification.passed is True
        # Should include logo-specific checks
        assert "logo" in verification.analysis.lower()

    def test_build_verification_context(self):
        """Test building verification context"""
        context = self.verifier._build_verification_context(
            original_prompt="Test prompt",
            enhanced_prompt="Enhanced test prompt",
            dialogue_responses={"style": "modern"},
            image_type="logo"
        )

        assert "original_prompt" in context
        assert "enhanced_prompt" in context
        assert "image_type" in context
        assert context["image_type"] == "logo"

    def test_build_verification_checklist(self):
        """Test building verification checklist"""
        context = {
            "original_prompt": "Create a logo",
            "image_type": "logo",
            "key_requirements": ["Minimalist style", "Blue colors"]
        }

        checklist = self.verifier._build_verification_checklist(context)

        assert len(checklist) > 0
        # Should have subject matter check
        assert any("subject" in item["item"].lower() for item in checklist)
        # Should have logo-specific check
        assert any("logo" in item["item"].lower() for item in checklist)
        # Should have quality check
        assert any("quality" in item["item"].lower() for item in checklist)

    def test_checklist_for_presentation(self):
        """Test checklist for presentation images"""
        context = {
            "original_prompt": "Slide background",
            "image_type": "presentation"
        }

        checklist = self.verifier._build_verification_checklist(context)

        # Should have presentation-specific check
        assert any("presentation" in item["item"].lower() for item in checklist)

    def test_checklist_for_social_media(self):
        """Test checklist for social media images"""
        context = {
            "original_prompt": "Instagram post",
            "image_type": "social_media"
        }

        checklist = self.verifier._build_verification_checklist(context)

        # Should have social media-specific check
        assert any("social" in item["item"].lower() for item in checklist)

    def test_format_verification_report(self):
        """Test formatting verification report"""
        verification = ImageVerification(
            passed=True,
            confidence=0.90,
            issues=[],
            suggestions=["Verify colors", "Check composition"],
            analysis="Image meets requirements"
        )

        report = self.verifier.format_verification_report(verification)

        assert "✅" in report  # Pass indicator
        assert "90%" in report  # Confidence
        assert "Suggestions:" in report
        assert "Verify colors" in report

    def test_format_report_with_issues(self):
        """Test formatting report with issues"""
        verification = ImageVerification(
            passed=False,
            confidence=0.50,
            issues=["Text missing", "Wrong style"],
            suggestions=["Add text", "Change style"],
            analysis="Issues detected"
        )

        report = self.verifier.format_verification_report(verification)

        assert "⚠️" in report  # Warning indicator
        assert "Issues Found:" in report
        assert "Text missing" in report
        assert "Wrong style" in report

    def test_format_report_without_analysis(self):
        """Test formatting report without detailed analysis"""
        verification = ImageVerification(
            passed=True,
            confidence=0.80,
            issues=[],
            suggestions=[],
            analysis="Brief analysis"
        )

        report = self.verifier.format_verification_report(
            verification,
            include_analysis=False
        )

        assert "✅" in report
        assert "Brief analysis" not in report

    def test_verification_disabled(self):
        """Test behavior when verification is disabled"""
        self.verifier.verification_enabled = False

        image_path = Path(self.temp_dir) / "test.png"
        image_path.write_bytes(b"test")

        verification = self.verifier.verify_image(
            image_path=str(image_path),
            original_prompt="Test",
            enhanced_prompt="Test enhanced"
        )

        assert verification.passed is True
        assert verification.confidence == 1.0
        assert "disabled" in verification.analysis.lower()


class TestGetImageVerifier:
    """Test the global verifier singleton"""

    def test_get_image_verifier_creates_instance(self):
        """Test that get_image_verifier returns an instance"""
        verifier = get_image_verifier()
        assert verifier is not None
        assert isinstance(verifier, ImageVerifier)

    def test_get_image_verifier_returns_same_instance(self):
        """Test that get_image_verifier returns the same instance"""
        verifier1 = get_image_verifier()
        verifier2 = get_image_verifier()
        assert verifier1 is verifier2


class TestVerificationWorkflows:
    """Test complete verification workflows"""

    def setup_method(self):
        self.verifier = ImageVerifier()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_logo_verification_workflow(self):
        """Test complete logo verification workflow"""
        image_path = Path(self.temp_dir) / "logo.png"
        image_path.write_bytes(b"fake logo data")

        dialogue_responses = {
            "initial": "Tech startup",
            "style": "Minimalist modern",
            "color_mood": "Professional blues",
            "composition": "Centered"
        }

        verification = self.verifier.verify_image(
            image_path=str(image_path),
            original_prompt="Create a tech company logo",
            enhanced_prompt="Modern minimalist tech company logo, professional blue color palette, centered composition",
            dialogue_responses=dialogue_responses,
            image_type="logo"
        )

        assert verification.passed is True
        assert "logo" in verification.analysis.lower()
        assert len(verification.suggestions) > 0

    def test_presentation_verification_workflow(self):
        """Test complete presentation verification workflow"""
        image_path = Path(self.temp_dir) / "slide.png"
        image_path.write_bytes(b"fake slide data")

        verification = self.verifier.verify_image(
            image_path=str(image_path),
            original_prompt="Presentation background",
            enhanced_prompt="Professional presentation background with high contrast",
            image_type="presentation"
        )

        assert verification.passed is True
        assert "presentation" in verification.analysis.lower()

    def test_social_media_verification_workflow(self):
        """Test complete social media verification workflow"""
        image_path = Path(self.temp_dir) / "post.png"
        image_path.write_bytes(b"fake social post")

        verification = self.verifier.verify_image(
            image_path=str(image_path),
            original_prompt="Instagram post about coffee",
            enhanced_prompt="Eye-catching Instagram post about coffee, vibrant colors",
            image_type="social_media"
        )

        assert verification.passed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
