#!/usr/bin/env python3
"""
Run Gemini File Extraction Tests and Output Results to File
Captures all test results and saves them to a text file for review.
"""
import sys
import os
import io
import unittest
from datetime import datetime
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gemini_file_extract import GeminiFileExtractor

def run_individual_tests():
    """Run individual test cases and capture detailed results"""
    results = []
    test_dir = Path(__file__).parent
    
    # Test files
    pdf_file = test_dir / "test_files" / "test_document.pdf"
    image_file = test_dir / "test_files" / "test_image.jpg"
    dummy_file = test_dir / "test_files" / "dummy_file.txt"
    nonexistent_file = test_dir / "nonexistent.pdf"
    
    try:
        extractor = GeminiFileExtractor()
        results.append("✅ Gemini File Extractor initialized successfully")
    except Exception as e:
        results.append(f"❌ Failed to initialize extractor: {str(e)}")
        return results
    
    # Test 1: PDF Extraction
    results.append("\n" + "="*80)
    results.append("TEST 1: PDF Document Extraction")
    results.append("="*80)
    
    if pdf_file.exists():
        try:
            result = extractor.extract_from_file(str(pdf_file))
            if result.success:
                results.append("✅ PDF extraction: SUCCESS")
                results.append(f"   File: {pdf_file.name}")
                results.append(f"   Description: {result.description}")
                results.append(f"   Content length: {len(result.result)} characters")
                results.append(f"   Content preview: {result.result[:200]}...")
            else:
                results.append("❌ PDF extraction: FAILED")
                results.append(f"   Error: {result.error}")
        except Exception as e:
            results.append(f"❌ PDF extraction: EXCEPTION - {str(e)}")
    else:
        results.append(f"❌ PDF test file not found: {pdf_file}")
    
    # Test 2: Image Extraction
    results.append("\n" + "="*80)
    results.append("TEST 2: Image Extraction")
    results.append("="*80)
    
    if image_file.exists():
        try:
            result = extractor.extract_from_file(str(image_file))
            if result.success:
                results.append("✅ Image extraction: SUCCESS")
                results.append(f"   File: {image_file.name}")
                results.append(f"   Description: {result.description}")
                results.append(f"   Content length: {len(result.result)} characters")
                results.append(f"   Content preview: {result.result[:200]}...")
            else:
                results.append("❌ Image extraction: FAILED")
                results.append(f"   Error: {result.error}")
        except Exception as e:
            results.append(f"❌ Image extraction: EXCEPTION - {str(e)}")
    else:
        results.append(f"❌ Image test file not found: {image_file}")
    
    # Test 3: Unsupported File Type
    results.append("\n" + "="*80)
    results.append("TEST 3: Unsupported File Type (Should Fail)")
    results.append("="*80)
    
    if dummy_file.exists():
        try:
            result = extractor.extract_from_file(str(dummy_file))
            if not result.success:
                results.append("✅ Unsupported file rejection: SUCCESS")
                results.append(f"   File: {dummy_file.name}")
                results.append(f"   Expected error: {result.error}")
            else:
                results.append("❌ Unsupported file rejection: FAILED (should have failed)")
                results.append(f"   Unexpected success: {result.description}")
        except Exception as e:
            results.append(f"❌ Unsupported file test: EXCEPTION - {str(e)}")
    else:
        results.append(f"❌ Dummy test file not found: {dummy_file}")
    
    # Test 4: Non-existent File
    results.append("\n" + "="*80)
    results.append("TEST 4: Non-existent File (Should Fail)")
    results.append("="*80)
    
    try:
        result = extractor.extract_from_file(str(nonexistent_file))
        if not result.success:
            results.append("✅ Non-existent file handling: SUCCESS")
            results.append(f"   File: {nonexistent_file.name}")
            results.append(f"   Expected error: {result.error}")
        else:
            results.append("❌ Non-existent file handling: FAILED (should have failed)")
            results.append(f"   Unexpected success: {result.description}")
    except Exception as e:
        results.append(f"❌ Non-existent file test: EXCEPTION - {str(e)}")
    
    return results

def main():
    """Main function to run tests and save results to file"""
    output_file = "test_results.txt"
    
    print(f"🚀 Running Gemini File Extraction Tests...")
    print(f"📝 Results will be saved to: {output_file}")
    
    # Capture test results
    results = []
    
    # Header
    results.append("GEMINI FILE EXTRACTION TEST RESULTS")
    results.append("="*80)
    results.append(f"Test Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append(f"Working Directory: {os.getcwd()}")
    results.append("")
    
    # File checks
    results.append("FILE AVAILABILITY CHECK")
    results.append("-"*40)
    test_files = [
        "test/test_files/test_document.pdf",
        "test/test_files/test_image.jpg", 
        "test/test_files/dummy_file.txt"
    ]
    
    for filename in test_files:
        file_path = Path(filename)
        if file_path.exists():
            size = file_path.stat().st_size
            results.append(f"✅ {filename} ({size:,} bytes)")
        else:
            results.append(f"❌ {filename} (NOT FOUND)")
    
    results.append("")
    
    # Run individual tests
    test_results = run_individual_tests()
    results.extend(test_results)
    
    # Summary
    results.append("\n" + "="*80)
    results.append("TEST SUMMARY")
    results.append("="*80)
    
    success_count = len([line for line in results if "SUCCESS" in line and "✅" in line])
    fail_count = len([line for line in results if ("FAILED" in line or "EXCEPTION" in line) and "❌" in line])
    
    results.append(f"Total Tests: {success_count + fail_count}")
    results.append(f"Successful: {success_count}")
    results.append(f"Failed: {fail_count}")
    
    if fail_count == 0:
        results.append("🎉 ALL TESTS PASSED!")
    else:
        results.append("⚠️  Some tests failed - check details above")
    
    results.append("")
    results.append("End of Test Report")
    results.append("="*80)

if __name__ == "__main__":
    main()