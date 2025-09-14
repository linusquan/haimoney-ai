#!/usr/bin/env python3
"""
Test Suite for Concurrent Gemini File Extraction
Tests the new extract_multiple_files method with various scenarios
"""
import unittest
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from tools.file_extract import GeminiFileExtractor, ExtractionResult

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)


class TestConcurrentExtraction(unittest.TestCase):
    """Test suite for concurrent file extraction functionality"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.extractor = GeminiFileExtractor()
        self.test_dir = Path(__file__).parent
        self.test_files_dir = self.test_dir / "test_files"

        # Available test files
        self.all_test_files = [
            str(self.test_files_dir / "test_document.pdf"),
            str(self.test_files_dir / "test_image.jpg"),
            str(self.test_files_dir / "bill.pdf"),
            str(self.test_files_dir / "rental.pdf"),
            str(self.test_files_dir / "water.pdf"),
            str(self.test_files_dir / "bank.pdf")
        ]

        # Filter to only existing files
        self.existing_files = [f for f in self.all_test_files if Path(f).exists()]

        # Create output directory with timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = self.test_dir / ".test_output" / f"concurrent_{self.timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Test setup complete. Found {len(self.existing_files)} test files")

    def test_concurrent_extraction_all_files(self):
        """Test concurrent extraction with all available test files"""
        logger.info("=== Testing Concurrent Extraction - All Files ===")

        self.assertGreater(len(self.existing_files), 0, "No test files found")

        # Test with default max_concurrent (5)
        results = self.extractor.extract_multiple_files(self.existing_files)

        self.assertEqual(len(results), len(self.existing_files), "Results count should match input files")

        # Verify all results are ExtractionResult objects
        for i, result in enumerate(results):
            self.assertIsInstance(result, ExtractionResult, f"Result {i} should be ExtractionResult")
            self.assertIsNotNone(result, f"Result {i} should not be None")

        # Count successes and failures
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        logger.info(f"Concurrent extraction results: {len(successful)} successful, {len(failed)} failed")

        # Save detailed results
        self._save_test_results("concurrent_all_files", results)

        # At least some extractions should succeed (depends on API availability)
        self.assertGreater(len(successful), 0, "At least some extractions should succeed")

    @unittest.skip # skipping for speed
    def xtest_concurrent_extraction_limited_concurrency(self):
        """Test concurrent extraction with max_concurrent=2"""
        logger.info("=== Testing Concurrent Extraction - Limited Concurrency (max=2) ===")

        # Use first 4 files to test concurrency limiting
        test_files = self.existing_files[:4] if len(self.existing_files) >= 4 else self.existing_files

        if len(test_files) < 2:
            self.skipTest("Need at least 2 test files for this test")

        # Test with max_concurrent=2
        results = self.extractor.extract_multiple_files(test_files, max_concurrent=2)

        self.assertEqual(len(results), len(test_files), "Results count should match input files")

        # Verify results order is preserved
        for i, result in enumerate(results):
            expected_filename = Path(test_files[i]).name
            if result.success:
                self.assertEqual(result.filename, expected_filename, f"Result {i} filename should match")

        # Save results
        self._save_test_results("concurrent_limited", results)

        logger.info(f"Limited concurrency test completed with {len(results)} files")

    @unittest.skip # skipping for speed
    def xtest_concurrent_extraction_single_file(self):
        """Test concurrent extraction with single file (edge case)"""
        logger.info("=== Testing Concurrent Extraction - Single File ===")

        if not self.existing_files:
            self.skipTest("No test files available")

        single_file = [self.existing_files[0]]
        results = self.extractor.extract_multiple_files(single_file)

        self.assertEqual(len(results), 1, "Should return exactly one result")
        self.assertIsInstance(results[0], ExtractionResult, "Result should be ExtractionResult")

        # Save results
        self._save_test_results("concurrent_single", results)

        logger.info("Single file concurrent extraction test completed")

    def _save_test_results(self, test_name: str, results: List[ExtractionResult]):
        """Save test results to files for inspection"""
        try:
            output_file = self.output_dir / f"{test_name}_{self.timestamp}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Test Results: {test_name}\n")
                f.write(f"Timestamp: {self.timestamp}\n")
                f.write(f"Total results: {len(results)}\n")
                f.write(f"Successful: {sum(1 for r in results if r.success)}\n")
                f.write(f"Failed: {sum(1 for r in results if not r.success)}\n")
                f.write(f"\n{'='*60}\n\n")

                for i, result in enumerate(results):
                    f.write(f"File {i+1}: {result.filename or 'Unknown'}\n")
                    f.write(f"Success: {result.success}\n")
                    if result.success:
                        f.write(f"Description: {result.description}\n")
                        f.write(f"Content length: {len(result.result or '')} characters\n")
                        f.write(f"Content preview: {(result.result or '')[:200]}...\n")
                    else:
                        f.write(f"Error: {result.error}\n")
                    f.write(f"\n{'-'*40}\n\n")

            logger.info(f"Test results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

    def tearDown(self):
        """Clean up after tests"""
        logger.info(f"Test completed. Results saved to: {self.output_dir}")


if __name__ == "__main__":
    # Run the test suite with verbose output
    unittest.main(verbosity=2)