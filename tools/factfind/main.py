#!/usr/bin/env python3
"""
Main Test Executor
Runs document extractions in two concurrent batches:
- Batch 1: basic_fact, asset, liability (concurrent)
- Batch 2: income, expense (concurrent, after Batch 1 completes)
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# No longer need to manipulate sys.path with absolute imports

from tools.factfind.basic.basic_fact import BasicFactAnalyser
from tools.factfind.asset.asset_extraction import AssetAnalyser
from tools.factfind.liability.liability_extraction import LiabilityAnalyser
from tools.factfind.income.income_extraction import IncomeAnalyser
from tools.factfind.expense.expense_extraction import ExpenseAnalyser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
logger = logging.getLogger(__name__)

def print_separator(title: str):
    """Print a formatted separator with title"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def ensure_output_directory():
    """Create output/result directory if it doesn't exist"""
    output_dir = Path("output/result")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def write_results_to_file(category_name: str, results, output_dir: Path):
    """Write results to JSON file in the output directory"""
    try:
        filename = f"{category_name}.json"
        filepath = output_dir / filename
        
        results_data = results.model_dump()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results written to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to write {category_name} results to file: {e}")
        return None

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
    """Main test function that runs extractors in two batches"""
    try:
        print_separator("DOCUMENT EXTRACTION TEST SUITE")
        
        # Ensure output directory exists
        output_dir = ensure_output_directory()
        logger.info(f"Output directory: {output_dir}")
        
        # BATCH 1: basic_fact, asset, liability (concurrent)
        print("BATCH 1: Running basic_fact, asset, and liability extractions in parallel...")
        logger.info("Initializing Batch 1 extractors...")
        
        batch1_extractors = {
            "basic_fact": BasicFactAnalyser(),
            "asset": AssetAnalyser(),
            "liability": LiabilityAnalyser()
        }
        
        logger.info("Starting Batch 1 parallel extraction...")
        batch1_results = run_extraction_parallel(batch1_extractors)
        
        # Display and save Batch 1 results
        if batch1_results.get("basic_fact"):
            print_json_results("BASIC FACT EXTRACTION RESULTS", batch1_results["basic_fact"])
            write_results_to_file("basic_fact", batch1_results["basic_fact"], output_dir)
        
        if batch1_results.get("asset"):
            print_json_results("ASSET EXTRACTION RESULTS", batch1_results["asset"])
            write_results_to_file("asset", batch1_results["asset"], output_dir)
        
        if batch1_results.get("liability"):
            print_json_results("LIABILITY EXTRACTION RESULTS", batch1_results["liability"])
            write_results_to_file("liability", batch1_results["liability"], output_dir)
        
        # BATCH 2: income, expense (concurrent)
        print("\nBATCH 2: Running income and expense extractions in parallel...")
        logger.info("Initializing Batch 2 extractors...")
        
        batch2_extractors = {
            "income": IncomeAnalyser(),
            "expense": ExpenseAnalyser()
        }
        
        logger.info("Starting Batch 2 parallel extraction...")
        batch2_results = run_extraction_parallel(batch2_extractors)
        
        # Display and save Batch 2 results
        if batch2_results.get("income"):
            print_json_results("INCOME EXTRACTION RESULTS", batch2_results["income"])
            write_results_to_file("income", batch2_results["income"], output_dir)
        
        if batch2_results.get("expense"):
            print_json_results("EXPENSE EXTRACTION RESULTS", batch2_results["expense"])
            write_results_to_file("expense", batch2_results["expense"], output_dir)
        
        print_separator("TEST COMPLETE")
        logger.info("All extractions completed successfully")
        logger.info(f"All results saved to: {output_dir}")
        return 0
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())