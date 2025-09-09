#!/usr/bin/env python3
"""
Main Test Executor
Runs basic fact extraction and asset extraction sequentially and displays results.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# No longer need to manipulate sys.path with absolute imports

from factfind.basic.basic_fact import BasicFactExtractor
from factfind.asset.asset_extraction import AssetExtractor

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

def run_extraction_parallel(extractors_config):
    """Run multiple extractors in parallel using ThreadPoolExecutor"""
    results = {}
    
    with ThreadPoolExecutor(max_workers=len(extractors_config)) as executor:
        # Submit all extraction tasks
        future_to_name = {
            executor.submit(extractor.run_extraction): name 
            for name, extractor in extractors_config.items()
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_name):
            extractor_name = future_to_name[future]
            try:
                result = future.result()
                results[extractor_name] = result
                logger.info(f"Completed {extractor_name} extraction")
            except Exception as exc:
                logger.error(f"{extractor_name} extraction failed: {exc}")
                results[extractor_name] = None
    
    return results

def main():
    """Main test function that runs both extractors"""
    try:
        print_separator("DOCUMENT EXTRACTION TEST SUITE")
        print("Running basic fact extraction and asset extraction in parallel...")
        
        # Initialize extractors for parallel execution
        logger.info("Initializing extractors...")
        extractors_config = {
            "basic_fact": BasicFactExtractor(),
            "asset": AssetExtractor()
        }
        
        # Run extractions in parallel
        logger.info("Starting parallel extraction...")
        results = run_extraction_parallel(extractors_config)
        
        # Display results
        if results.get("basic_fact"):
            print_json_results("BASIC FACT EXTRACTION RESULTS", results["basic_fact"])
        
        if results.get("asset"):
            print_json_results("ASSET EXTRACTION RESULTS", results["asset"])
        
        # # Run liability extraction
        # logger.info("Starting liability extraction...")
        # liability_results = liability_extractor.run_extraction()
        # print_json_results("LIABILITY EXTRACTION RESULTS", liability_results)
        
        # # Run income extraction
        # logger.info("Starting income extraction...")
        # income_results = income_extractor.run_extraction()
        # print_json_results("INCOME EXTRACTION RESULTS", income_results)
        
        # Run expense extraction
        # logger.info("Starting expense extraction...")
        # expense_results = expense_extractor.run_extraction()
        # print_json_results("EXPENSE EXTRACTION RESULTS", expense_results)
        
        print_separator("TEST COMPLETE")
        logger.info("All extractions completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())