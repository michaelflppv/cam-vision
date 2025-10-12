"""Unit tests for OCR text cleaning logic."""

from __future__ import annotations

import pytest

from cam_vision.plates.ocr import TesseractOCR


class TestOCRTextCleaning:
    """Test OCR text cleaning and post-processing."""

    def test_basic_cleaning_with_uppercase(self):
        """Test basic text cleaning with uppercase conversion."""
        ocr = TesseractOCR(
            to_uppercase=True,
            strip_whitespace=True,
            substitute_o_to_0=False,
            substitute_i_to_1=False,
        )

        # Test lowercase → uppercase
        assert ocr._clean_text("abc123") == "ABC123"

        # Test with spaces
        assert ocr._clean_text("ABC 123") == "ABC123"

        # Test with tabs and newlines
        assert ocr._clean_text("ABC\t123\n") == "ABC123"

    def test_whitespace_stripping_disabled(self):
        """Test cleaning with whitespace stripping disabled."""
        ocr = TesseractOCR(
            to_uppercase=True,
            strip_whitespace=False,  # Keep whitespace
            char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ",  # Includes space
        )

        # Spaces are now in the default whitelist, so they're preserved
        result = ocr._clean_text("ABC 123")
        assert result == "ABC 123"  # Space is preserved (in whitelist)

    def test_uppercase_disabled(self):
        """Test cleaning with uppercase conversion disabled."""
        ocr = TesseractOCR(
            to_uppercase=False,
            strip_whitespace=True,
        )

        # Should preserve case but still apply regex
        result = ocr._clean_text("AbC123")
        # Lowercase letters not in default whitelist → removed
        assert result == "AC123"

    def test_o_to_0_substitution(self):
        """Test letter O → digit 0 substitution."""
        ocr = TesseractOCR(
            to_uppercase=True,
            substitute_o_to_0=True,
        )

        assert ocr._clean_text("ABC0123") == "ABC0123"  # Already 0
        assert ocr._clean_text("ABCO123") == "ABC0123"  # O → 0
        assert ocr._clean_text("OOOO") == "0000"  # Multiple Os

    def test_i_to_1_substitution(self):
        """Test letter I → digit 1 substitution."""
        ocr = TesseractOCR(
            to_uppercase=True,
            substitute_i_to_1=True,
        )

        assert ocr._clean_text("ABC1123") == "ABC1123"  # Already 1
        assert ocr._clean_text("ABCI123") == "ABC1123"  # I → 1
        assert ocr._clean_text("IIII") == "1111"  # Multiple Is

    def test_both_substitutions(self):
        """Test both O→0 and I→1 substitutions together."""
        ocr = TesseractOCR(
            to_uppercase=True,
            substitute_o_to_0=True,
            substitute_i_to_1=True,
        )

        assert ocr._clean_text("OI01") == "0101"
        assert ocr._clean_text("OHIO") == "0H10"
        assert ocr._clean_text("IOU") == "10U"

    def test_regex_removes_special_chars(self):
        """Test that regex removes non-whitelisted characters."""
        ocr = TesseractOCR(
            to_uppercase=True,
            char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        )

        # Special characters should be removed
        assert ocr._clean_text("ABC-123") == "ABC123"
        assert ocr._clean_text("ABC_123") == "ABC123"
        assert ocr._clean_text("ABC.123") == "ABC123"
        assert ocr._clean_text("ABC@123!") == "ABC123"

    def test_regex_with_custom_whitelist(self):
        """Test regex cleaning with custom character whitelist."""
        ocr = TesseractOCR(
            to_uppercase=True,
            char_whitelist="ABC123",  # Very limited whitelist
        )

        assert ocr._clean_text("ABC123") == "ABC123"
        assert ocr._clean_text("ABCXYZ123") == "ABC123"  # X, Y, Z removed
        assert ocr._clean_text("ABC456") == "ABC"  # 4, 5, 6 removed

    def test_empty_and_whitespace_only_input(self):
        """Test cleaning empty and whitespace-only strings."""
        ocr = TesseractOCR(to_uppercase=True, strip_whitespace=True)

        assert ocr._clean_text("") == ""
        assert ocr._clean_text("   ") == ""
        assert ocr._clean_text("\t\n") == ""

    def test_realistic_plate_scenarios(self):
        """Test realistic license plate OCR scenarios."""
        ocr = TesseractOCR(
            to_uppercase=True,
            strip_whitespace=True,
            substitute_o_to_0=False,
            substitute_i_to_1=False,
        )

        # Common OCR outputs - space and hyphen are now in default whitelist
        assert ocr._clean_text("AB C-123") == "ABC-123"  # Hyphen preserved
        assert ocr._clean_text("ABC 123") == "ABC123"  # Space stripped (strip_whitespace=True)
        assert ocr._clean_text("abc-123") == "ABC-123"  # Hyphen preserved
        assert ocr._clean_text(" ABC123 ") == "ABC123"

    def test_realistic_plate_with_substitutions(self):
        """Test realistic plates with O/I substitutions."""
        ocr = TesseractOCR(
            to_uppercase=True,
            substitute_o_to_0=True,
            substitute_i_to_1=True,
        )

        # Common OCR errors
        assert ocr._clean_text("OHIO123") == "0H10123"  # O → 0, I → 1
        assert ocr._clean_text("CALI456") == "CAL1456"  # I → 1
        assert ocr._clean_text("FL0RIDA") == "FL0R1DA"  # O already 0, I → 1

    def test_min_text_length_in_ocr_settings(self):
        """Test min_text_length setting (used in pipeline, not _clean_text)."""
        ocr = TesseractOCR(min_text_length=5)

        # Just verify setting is stored
        assert ocr.min_text_length == 5

        # Cleaning doesn't enforce length (pipeline does)
        assert ocr._clean_text("AB") == "AB"

    def test_sequential_processing(self):
        """Test that cleaning steps are applied in correct order."""
        ocr = TesseractOCR(
            to_uppercase=True,
            strip_whitespace=True,
            substitute_o_to_0=True,
            substitute_i_to_1=True,
            char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        )

        # Input: lowercase with spaces, has O and I
        raw = "ab c-o1i 5"

        # Expected processing:
        # 1. Strip whitespace: "abc-o1i5"
        # 2. Uppercase: "ABC-O1I5"
        # 3. O→0: "ABC-01I5"
        # 4. I→1: "ABC-0115"
        # 5. Regex (remove -): "ABC0115"

        assert ocr._clean_text(raw) == "ABC0115"

    def test_unicode_and_special_cases(self):
        """Test handling of unicode and edge cases."""
        ocr = TesseractOCR(to_uppercase=True)

        # Accented characters not in whitelist → removed
        assert ocr._clean_text("CAFÉ123") == "CAF123"

        # Emoji → removed
        assert ocr._clean_text("ABC123😀") == "ABC123"

        # Non-breaking space → removed (not in whitelist)
        assert ocr._clean_text("ABC\u00A0123") == "ABC123"


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("ABC123", "ABC123"),
        ("abc123", "ABC123"),
        ("ABC-123", "ABC-123"),  # Hyphen now in default whitelist
        ("AB C 123", "ABC123"),  # Space stripped by strip_whitespace=True
        ("  ABC123  ", "ABC123"),
        ("", ""),
        ("@#$%", ""),
        ("XYZ789", "XYZ789"),
    ],
)
def test_cleaning_parametrized(input_text: str, expected: str):
    """Parametrized test for common cleaning scenarios."""
    ocr = TesseractOCR(to_uppercase=True, strip_whitespace=True)
    assert ocr._clean_text(input_text) == expected
