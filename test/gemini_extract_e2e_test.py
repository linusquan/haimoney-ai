#!/usr/bin/env python3
"""
E2E Test Suite for Gemini File Extraction
"""
import unittest
from pathlib import Path
from datetime import datetime

from tools.file_extract import GeminiFileExtractor


class TestGeminiFileExtraction(unittest.TestCase):
    """Test suite for Gemini file extraction functionality"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.extractor = GeminiFileExtractor()
        self.test_dir = Path(__file__).parent
        self.pdf_file = self.test_dir / "test_files" / "test_document.pdf"
        self.image_file = self.test_dir / "test_files" / "test_image.jpg"

        # Create output directory with timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = self.test_dir / ".test_output" / self.timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)


    def test_pdf_extraction(self):
        """Test PDF document extraction"""
        self.assertTrue(self.pdf_file.exists(), f"PDF test file not found: {self.pdf_file}")

        result = self.extractor.extract_from_file(str(self.pdf_file))

        self.assertTrue(result.success, f"PDF extraction failed: {result.error}")
        self.assertIsNotNone(result.result, "PDF extraction result is None")
        self.assertGreater(len(result.result), 0, "PDF extraction result is empty")
        self.assertIsNotNone(result.description, "PDF extraction description is None")

        # Store result to file
        output_file = self.output_dir / f"pdf_extraction_{self.timestamp}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"PDF Extraction Test Results\n")
            f.write(f"Timestamp: {self.timestamp}\n")
            f.write(f"File: {self.pdf_file.name}\n")
            f.write(f"Description: {result.description}\n")
            f.write(f"Content length: {len(result.result)} characters\n")
            f.write(f"\n--- EXTRACTED CONTENT ---\n")
            f.write(result.result)

        print(f"PDF extraction successful:")

    def test_image_extraction(self):
        """Test image extraction"""
        self.assertTrue(self.image_file.exists(), f"Image test file not found: {self.image_file}")

        result = self.extractor.extract_from_file(str(self.image_file))

        self.assertTrue(result.success, f"Image extraction failed: {result.error}")
        self.assertIsNotNone(result.result, "Image extraction result is None")
        self.assertGreater(len(result.result), 0, "Image extraction result is empty")
        self.assertIsNotNone(result.description, "Image extraction description is None")

        # Store result to file
        output_file = self.output_dir / f"image_extraction_{self.timestamp}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Image Extraction Test Results\n")
            f.write(f"Timestamp: {self.timestamp}\n")
            f.write(f"File: {self.image_file.name}\n")
            f.write(f"Description: {result.description}\n")
            f.write(f"Content length: {len(result.result)} characters\n")
            f.write(f"\n--- EXTRACTED CONTENT ---\n")
            f.write(result.result)
        print(f"Image extraction successful:")

    def tearDown(self):
        """Clean up after tests and print summary"""
        print(f"\nTest Summary:")
        print(f"  Output Directory: {self.output_dir}")


if __name__ == "__main__":
    # Run the test suite with verbose output
    unittest.main(verbosity=2, exit=False)
    print("\nAll tests completed. Check .test_output directory for detailed results.")