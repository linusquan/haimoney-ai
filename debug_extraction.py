#!/usr/bin/env python3
"""
Debug Script for Gemini File Extraction
Test extraction with rental.pdf and debug any JSON parsing issues
"""
import os
import sys
import json
import logging
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

from tools.file_extract import GeminiFileExtractor, ExtractionResult

def debug_single_extraction():
    """Debug extraction of rental.pdf file"""

    # File to debug
    test_file = "/Users/liquan/code/haimoney-ai/test/test_files/rental.pdf"

    print("=" * 60)
    print("DEBUG: Gemini File Extraction")
    print("=" * 60)

    # Check if file exists
    if not os.path.exists(test_file):
        print(f"ERROR: File not found: {test_file}")
        return

    print(f"Target file: {test_file}")
    print(f"File size: {os.path.getsize(test_file):,} bytes")
    print()

    try:
        # Initialize extractor
        print("Initializing GeminiFileExtractor...")
        extractor = GeminiFileExtractor()
        print("Extractor initialized successfully")
        print()

        # Perform extraction
        print("Starting extraction...")
        result = extractor.extract_from_file(test_file)
        print()

        # Debug the result
        print("EXTRACTION RESULT:")
        print("-" * 40)
        print(f"Success: {result.success}")
        print(f"File Path: {result.file_path}")
        print(f"Filename: {result.filename}")
        print()

        if result.success:
            print("SUCCESSFUL EXTRACTION")
            print(f"Description: {result.description}")
            print()
            print("EXTRACTED CONTENT:")
            print("-" * 40)
            if result.result:
                # Print first 500 characters for debugging
                content = result.result
                print(f"Content length: {len(content)} characters")
                print()
                print("First 500 characters:")
                print(repr(content[:500]))  # Use repr to show escape characters
                print()
                print("Formatted preview:")
                print(content[:500])

                # Check for problematic characters
                print("\nCHARACTER ANALYSIS:")
                print("-" * 40)
                carriage_returns = content.count('\r')
                newlines = content.count('\n')
                backslash_r = content.count('\\r')

                print(f"Carriage returns (\\r): {carriage_returns}")
                print(f"Newlines (\\n): {newlines}")
                print(f"Literal \\r strings: {backslash_r}")

                if carriage_returns > 0:
                    print("WARNING: Found carriage return characters - these may cause JSON parsing issues")

                # Try to create a JSON object to test
                print("\nJSON VALIDATION TEST:")
                print("-" * 40)
                try:
                    test_json = {
                        "description": result.description,
                        "error": False,
                        "errorReason": "",
                        "result": result.result
                    }
                    json_str = json.dumps(test_json, indent=2)
                    print("JSON serialization successful")

                    # Try to parse it back
                    parsed = json.loads(json_str)
                    print("JSON parsing successful")

                except Exception as json_error:
                    print(f"JSON error: {json_error}")

                    # Try with cleaned content
                    print("\nATTEMPTING CONTENT CLEANUP:")
                    cleaned_content = result.result.replace('\r\n', '\n').replace('\r', '\n')
                    try:
                        cleaned_json = {
                            "description": result.description,
                            "error": False,
                            "errorReason": "",
                            "result": cleaned_content
                        }
                        cleaned_str = json.dumps(cleaned_json, indent=2)
                        print("Cleaned JSON serialization successful")

                        # Save cleaned version for inspection
                        output_file = "debug_cleaned_extraction.json"
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(cleaned_str)
                        print(f"Cleaned result saved to: {output_file}")

                    except Exception as clean_error:
                        print(f"Cleaned JSON still failed: {clean_error}")
            else:
                print("WARNING: No content extracted")

        else:
            print("EXTRACTION FAILED")
            print(f"Error: {result.error}")

        # Save raw result for inspection
        output_file = "debug_raw_extraction.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Extraction Debug Results\n")
            f.write(f"========================\n\n")
            f.write(f"File: {test_file}\n")
            f.write(f"Success: {result.success}\n")
            f.write(f"Filename: {result.filename}\n")
            f.write(f"Description: {result.description}\n")
            f.write(f"Error: {result.error}\n\n")
            if result.result:
                f.write(f"Raw Content:\n")
                f.write(f"------------\n")
                f.write(result.result)

        print(f"\nRaw debug results saved to: {output_file}")

    except Exception as e:
        logger.error(f"Unexpected error during debug: {e}")
        import traceback
        traceback.print_exc()

def debug_concurrent_extraction():
    """Debug concurrent extraction with multiple files"""

    test_files = [
        "/Users/liquan/code/haimoney-ai/test/test_files/rental.pdf",
        "/Users/liquan/code/haimoney-ai/test/test_files/bill.pdf"
    ]

    # Filter to existing files
    existing_files = [f for f in test_files if os.path.exists(f)]

    if not existing_files:
        print("ERROR: No test files found for concurrent extraction")
        return

    print("\n" + "=" * 60)
    print("DEBUG: Concurrent Extraction")
    print("=" * 60)
    print(f"Files to process: {len(existing_files)}")
    for f in existing_files:
        print(f"  - {os.path.basename(f)}")
    print()

    try:
        extractor = GeminiFileExtractor()
        print("Starting concurrent extraction with max_concurrent=2...")

        results = extractor.extract_multiple_files(existing_files, max_concurrent=2)

        print(f"\nCONCURRENT RESULTS: {len(results)} files processed")
        print("-" * 40)

        for i, result in enumerate(results):
            print(f"\nFile {i+1}: {result.filename}")
            print(f"  Success: {result.success}")
            if result.success:
                print(f"  Content length: {len(result.result) if result.result else 0} characters")
                print(f"  Description: {result.description}")
            else:
                print(f"  Error: {result.error}")

        # Save concurrent results
        output_file = "debug_concurrent_results.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Concurrent Extraction Debug Results\n")
            f.write(f"===================================\n\n")
            f.write(f"Files processed: {len(results)}\n\n")

            for i, result in enumerate(results):
                f.write(f"File {i+1}: {result.filename}\n")
                f.write(f"Success: {result.success}\n")
                f.write(f"Description: {result.description}\n")
                f.write(f"Error: {result.error}\n")
                if result.result:
                    f.write(f"Content length: {len(result.result)} characters\n")
                    f.write(f"Content preview (first 200 chars):\n{result.result[:200]}\n")
                f.write(f"\n{'-'*40}\n\n")

        print(f"\nConcurrent debug results saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error during concurrent debug: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main debug function"""
    print("Gemini File Extraction Debugger")
    print("Choose debugging mode:")
    print("1. Debug single file extraction (rental.pdf)")
    print("2. Debug concurrent extraction (rental.pdf + bill.pdf)")
    print("3. Both")

    choice = input("\nEnter choice (1/2/3) or press Enter for single file: ").strip()

    if choice in ['1', '']:
        debug_single_extraction()
    elif choice == '2':
        debug_concurrent_extraction()
    elif choice == '3':
        debug_single_extraction()
        debug_concurrent_extraction()
    else:
        print("Invalid choice, running single file debug...")
        debug_single_extraction()

if __name__ == "__main__":
    main()