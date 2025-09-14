#!/usr/bin/env python3
"""
Test script for BasicFactAnalyser
Tests the basic fact extraction with files from /Users/liquan/code/haimoney-ai/test/test_files/extracts
"""

import json
import logging
from pathlib import Path
from datetime import datetime

# Import the BasicFactAnalyser
from tools.factfind.basic.basic_fact import BasicFactAnalyser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def print_separator(title: str):
    """Print a formatted separator with title"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_json_results(title: str, results):
    """Print JSON results with formatting"""
    print_separator(title)
    results_json = json.dumps(results.model_dump(), indent=2, ensure_ascii=False)
    print(results_json)

def save_results_to_file(results, output_dir: Path):
    """Save results to JSON file"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"basic_fact_test_{timestamp}.json"
        filepath = output_dir / filename

        results_data = results.model_dump()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save results to file: {e}")
        return None

def main():
    """Main test function"""
    try:
        print_separator("BASIC FACT ANALYSER TEST")

        # Define paths
        extraction_dir = "/Users/liquan/code/haimoney-ai/test/test_files/extracts/identity"
        output_dir = Path("output/test_results")

        logger.info(f"Testing BasicFactAnalyser with extraction_dir: {extraction_dir}")
        logger.info(f"Output directory: {output_dir}")

        # Verify extraction directory exists
        if not Path(extraction_dir).exists():
            raise FileNotFoundError(f"Extraction directory does not exist: {extraction_dir}")

        # Initialize the BasicFactAnalyser
        logger.info("Initializing BasicFactAnalyser...")
        analyser = BasicFactAnalyser()

        # Run the extraction
        logger.info("Starting basic fact extraction...")
        results = analyser.run_extraction(extraction_dir)

        # Display results
        print_json_results("BASIC FACT EXTRACTION RESULTS", results)

        # Save results to file
        save_results_to_file(results, output_dir)

        print_separator("TEST COMPLETED SUCCESSFULLY")
        logger.info("Basic fact extraction test completed successfully")

        return 0

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nERROR: {e}")
        print_separator("TEST FAILED")
        return 1

if __name__ == "__main__":
    exit(main())