#!/usr/bin/env python3
"""
Extract and Basic Analysis Test
Proper unit tests for the LLM File Analysis Service using unittest framework.

Test Configuration:
- Input: /Users/liquan/code/haimoney-ai/test/test_files/extract-analysis-basic
- Output: .test_output/extract_and_basic_analysis
- Category: basic analysis
"""

import unittest
import shutil
import logging
from pathlib import Path


from service.llm_file_analysis import LLMFileAnalysisService, LLMAnalysisResult

class TestExtractAndBasicAnalysis(unittest.TestCase):
    """Test cases for LLM File Analysis Service - Extract and Basic Analysis"""

    @classmethod
    def setUpClass(cls):
        """Set up test class with configuration"""
        cls.input_folder = Path(__file__).parent / "test_files/extract-analysis-basic"
        cls.output_dir = Path(__file__).parent / ".test_output/basic_output"
        cls.category = "basic"
        cls.supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

        # Setup logging
        cls._setup_logging()

    @classmethod
    def _setup_logging(cls):
        """Configure logging for tests"""
        log_dir = Path(__file__).parent / ".test_output"
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_dir / 'test_extract_and_basic_analysis.log')
            ]
        )

    def setUp(self):
        """Set up each test"""
        # Clear output directory before each test
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def test_extract_and_basic_analysis_integration(self):
        """Integration test for complete extract and basic analysis pipeline"""
        service = LLMFileAnalysisService(output_dir=str(self.output_dir))

        # Run the analysis
        result = service.analyze_files(str(self.input_folder), self.category)

        # Test result object
        self.assertIsInstance(result, LLMAnalysisResult, "Should return LLMAnalysisResult object")

        # Test success
        if not result.success:
            self.fail(f"Analysis should succeed, but got error: {result.error}")

        # Test basic result properties
        self.assertTrue(result.success, "Analysis should be successful")
        self.assertIsNotNone(result.analysis_id, "Should have analysis ID")
        self.assertGreater(result.files_processed, 0, "Should process at least one file")
        self.assertGreater(result.duration_seconds, 0, "Should take some time to process")

        # Test extraction results
        self.assertIsNotNone(result.extraction_results, "Should have extraction results")
        self.assertGreater(len(result.extraction_results), 0, "Should have at least one extraction result")

        successful_extractions = sum(1 for r in result.extraction_results if r['success'])
        self.assertGreater(successful_extractions, 0, "Should have at least one successful extraction")

        # Test category analysis
        self.assertIsNotNone(result.category_analysis, "Should have category analysis results")
        self.assertIn("category", result.category_analysis, "Should have category field in analysis results")
        self.assertEqual(result.category_analysis["category"], self.category, f"Should be {self.category} analysis")

        # Test output files exist
        extraction_dir = self.output_dir / f"extraction-{result.analysis_id}"
        self.assertTrue(extraction_dir.exists(), "Extraction directory should exist")

        basic_result_file = self.output_dir / f"basic-{result.analysis_id}.json"
        self.assertTrue(basic_result_file.exists(), "Basic analysis result file should exist")

        # Test extraction directory contents
        md_files = list(extraction_dir.glob("*.md"))
        metadata_files = list(extraction_dir.glob("*-hmoney-metadata.json"))

        self.assertGreater(len(md_files), 0, "Should have markdown files")
        self.assertGreater(len(metadata_files), 0, "Should have metadata files")

        print(f"\n✅ Integration test passed!")
        print(f"   Analysis ID: {result.analysis_id}")
        print(f"   Files processed: {result.files_processed}")
        print(f"   Duration: {result.duration_seconds:.2f} seconds")
        print(f"   Successful extractions: {successful_extractions}/{len(result.extraction_results)}")
        print(f"   Output directory: {self.output_dir}")

if __name__ == "__main__":
    unittest.main(verbosity=2)