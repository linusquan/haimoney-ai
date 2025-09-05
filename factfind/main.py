#!/usr/bin/env python3
"""
Main Test Executor
Runs basic fact extraction and asset extraction sequentially and displays results.
"""

import json
import logging
import sys
from pathlib import Path

# Add current directory to path to import extractors
sys.path.append(str(Path(__file__).parent))

from basic_fact import BasicFactExtractor
from asset_extraction import AssetExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

def main():
    """Main test function that runs both extractors"""
    try:
        print_separator("DOCUMENT EXTRACTION TEST SUITE")
        print("Running basic fact extraction and asset extraction sequentially...")
        
        # Initialize extractors
        logger.info("Initializing extractors...")
        basic_fact_extractor = BasicFactExtractor()
        asset_extractor = AssetExtractor()
        
        # Run basic fact extraction
        logger.info("Starting basic fact extraction...")
        basic_fact_results = basic_fact_extractor.run_extraction()
        print_json_results("BASIC FACT EXTRACTION RESULTS", basic_fact_results)
        
        # Run asset extraction
        logger.info("Starting asset extraction...")
        asset_results = asset_extractor.run_extraction()
        print_json_results("ASSET EXTRACTION RESULTS", asset_results)
        
        print_separator("TEST COMPLETE")
        logger.info("All extractions completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())