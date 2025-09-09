#!/usr/bin/env python3
"""
Main Test Executor
Runs basic fact extraction and asset extraction sequentially and displays results.
"""

import json
import logging

# No longer need to manipulate sys.path with absolute imports

from factfind.basic.basic_fact import BasicFactExtractor
from factfind.asset.asset_extraction import AssetExtractor
from factfind.liability.liability_extraction import LiabilityExtractor
from factfind.income.income_extraction import IncomeExtractor
from factfind.expense.expense_extraction import ExpenseExtractor

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
        print("Running basic fact extraction, asset extraction, liability extraction, income extraction, and expense extraction sequentially...")
        
        # Initialize extractors
        # logger.info("Initializing extractors...")
        basic_fact_extractor = BasicFactExtractor()
        asset_extractor = AssetExtractor()
        liability_extractor = LiabilityExtractor()
        income_extractor = IncomeExtractor()
        expense_extractor = ExpenseExtractor()
        
        # Run basic fact extraction
        # logger.info("Starting basic fact extraction...")
        # basic_fact_results = basic_fact_extractor.run_extraction()
        # print_json_results("BASIC FACT EXTRACTION RESULTS", basic_fact_results)
        
        # # Run asset extraction
        # logger.info("Starting asset extraction...")
        # asset_results = asset_extractor.run_extraction()
        # print_json_results("ASSET EXTRACTION RESULTS", asset_results)
        
        # # Run liability extraction
        # logger.info("Starting liability extraction...")
        # liability_results = liability_extractor.run_extraction()
        # print_json_results("LIABILITY EXTRACTION RESULTS", liability_results)
        
        # # Run income extraction
        # logger.info("Starting income extraction...")
        # income_results = income_extractor.run_extraction()
        # print_json_results("INCOME EXTRACTION RESULTS", income_results)
        
        # Run expense extraction
        logger.info("Starting expense extraction...")
        expense_results = expense_extractor.run_extraction()
        print_json_results("EXPENSE EXTRACTION RESULTS", expense_results)
        
        print_separator("TEST COMPLETE")
        logger.info("All extractions completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())