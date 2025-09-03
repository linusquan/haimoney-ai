#!/usr/bin/env python3
"""
Execute Gemini File Extraction Tests and Dump Full Output
Creates a comprehensive test results file in the extraction folder.
"""
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
from gemini_file_extract import GeminiFileExtractor

def dump_raw_extraction_results():
    """Simply dump raw extraction results for manual review"""
    output_lines = []
    
    # Ensure we're in the extraction directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Simple header
    output_lines.append("GEMINI FILE EXTRACTION - RAW RESPONSE DUMP")
    output_lines.append("=" * 80)
    output_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append("")
    
    # Initialize extractor
    try:
        extractor = GeminiFileExtractor()
    except Exception as e:
        output_lines.append(f"ERROR: Failed to initialize extractor: {str(e)}")
        return output_lines
    
    # Files to process
    files_to_extract = [
        "test_files/test_document.pdf",
        "test_files/test_image.jpg"
    ]
    
    # Process each file
    for file_path in files_to_extract:
        output_lines.append(f"FILE: {file_path}")
        output_lines.append("=" * 80)
        
        if not Path(file_path).exists():
            output_lines.append("ERROR: File not found")
            output_lines.append("")
            continue
        
        try:
            result = extractor.extract_from_file(file_path)
            
            if result.success:
                output_lines.append("EXTRACTION SUCCESSFUL")
                output_lines.append("")
                output_lines.append("DESCRIPTION:")
                output_lines.append(result.description)
                output_lines.append("")
                output_lines.append("FULL EXTRACTED CONTENT:")
                output_lines.append("-" * 80)
                output_lines.append(result.result)
                output_lines.append("-" * 80)
            else:
                output_lines.append("EXTRACTION FAILED")
                output_lines.append(f"Error: {result.error}")
                
        except Exception as e:
            output_lines.append(f"EXCEPTION OCCURRED: {str(e)}")
            output_lines.append("TRACEBACK:")
            output_lines.append(traceback.format_exc())
        
        output_lines.append("")
        output_lines.append("")
    
    return output_lines

def main():
    """Main execution function"""
    print("🔍 Dumping raw Gemini extraction results...")
    
    # Run extraction and capture output
    raw_output = dump_raw_extraction_results()
    
    # Write to file in current directory (extraction folder)
    output_filename = "gemini_raw_extraction_dump.txt"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(raw_output))
        
        print(f"✅ Raw extraction results saved to: {output_filename}")
        print(f"📁 File location: {os.path.abspath(output_filename)}")
        
    except Exception as e:
        print(f"❌ Failed to write output file: {str(e)}")
        print("Printing output to console instead:")
        print('\n'.join(raw_output))

if __name__ == "__main__":
    main()