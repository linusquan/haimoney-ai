#!/usr/bin/env python3
"""
File Extractor Script
Retrieves files from output/user_upload directory, extracts content using Gemini AI,
and saves results as markdown files with metadata.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Add the extraction directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'extraction'))

from gemini_file_extract import GeminiFileExtractor, ExtractionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('extractor.log')
    ]
)
logger = logging.getLogger(__name__)

class FileProcessor:
    def __init__(self, input_dir: str = "output/user_upload", output_dir: str = None, timeout_seconds: int = 120):
        """
        Initialize the file processor
        
        Args:
            input_dir: Directory containing files to process
            output_dir: Directory to save extracted files (defaults to same as input_dir)
            timeout_seconds: Timeout for each file extraction (default: 2 minutes)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir) if output_dir else self.input_dir
        self.timeout_seconds = timeout_seconds
        self.extractor = None
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize extractor
        try:
            self.extractor = GeminiFileExtractor()
            logger.info("✅ Gemini File Extractor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini extractor: {e}")
            raise

    def discover_files(self) -> List[Path]:
        """
        Discover all files in the input directory
        
        Returns:
            List of file paths to process
        """
        if not self.input_dir.exists():
            logger.error(f"❌ Input directory does not exist: {self.input_dir}")
            return []
        
        files = []
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        for file_path in self.input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(file_path)
        
        logger.info(f"📁 Discovered {len(files)} files to process")
        return sorted(files)

    def get_output_paths(self, input_file: Path) -> tuple[Path, Path]:
        """
        Generate output paths for markdown file and metadata JSON
        
        Args:
            input_file: Input file path
            
        Returns:
            Tuple of (markdown_path, metadata_path)
        """
        base_name = input_file.stem
        md_path = self.output_dir / f"{base_name}.md"
        metadata_path = self.output_dir / f"{base_name}-hmoney-metadata.json"
        return md_path, metadata_path

    def extract_with_timeout(self, file_path: Path) -> tuple[ExtractionResult, float]:
        """
        Extract file content with timeout handling
        
        Args:
            file_path: Path to file to extract
            
        Returns:
            Tuple of (ExtractionResult object, duration_seconds)
        """
        def extraction_task():
            return self.extractor.extract_from_file(str(file_path))
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(extraction_task)
            try:
                result = future.result(timeout=self.timeout_seconds)
                duration = time.time() - start_time
                return result, duration
            except TimeoutError:
                duration = time.time() - start_time
                logger.warning(f"⏰ Extraction timeout for {file_path.name}")
                return ExtractionResult.error_result(
                    f"Extraction timeout after {self.timeout_seconds} seconds",
                    str(file_path),
                    file_path.name
                ), duration
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ Extraction error for {file_path.name}: {e}")
                return ExtractionResult.error_result(
                    str(e),
                    str(file_path),
                    file_path.name
                ), duration

    def save_results(self, result: ExtractionResult, md_path: Path, metadata_path: Path, duration_seconds: float = 0.0) -> bool:
        """
        Save extraction results to markdown and metadata files
        
        Args:
            result: ExtractionResult object
            md_path: Path to save markdown content
            metadata_path: Path to save metadata JSON
            duration_seconds: Time taken for extraction
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare metadata
            metadata = {
                "filename": result.filename or md_path.stem,
                "description": result.description or "",
                "error": not result.success,
                "errorReason": result.error or "",
                "duration_seconds": round(duration_seconds, 2)
            }
            
            # Save metadata JSON
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Save markdown content
            if result.success and result.result:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(result.result)
                logger.info(f"💾 Saved: {md_path.name}")
            else:
                # Create empty markdown file for failed extractions
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Extraction Failed\n\n**Error:** {result.error}\n")
                logger.warning(f"⚠️  Failed extraction saved: {md_path.name}")
            
            logger.info(f"📋 Metadata saved: {metadata_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save results for {md_path.name}: {e}")
            return False

    def process_file(self, file_path: Path, index: int, total: int) -> Dict[str, Any]:
        """
        Process a single file: extract content and save results
        
        Args:
            file_path: Path to file to process
            index: Current file index (1-based)
            total: Total number of files
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"🔍 [{index}/{total}] Processing: {file_path.name}")
        
        # Get output paths
        md_path, metadata_path = self.get_output_paths(file_path)
        
        # Extract content with timeout
        result, duration = self.extract_with_timeout(file_path)
        
        # Save results
        save_success = self.save_results(result, md_path, metadata_path, duration)
        
        # Prepare summary
        summary = {
            "file": file_path.name,
            "success": result.success,
            "extraction_error": result.error if not result.success else None,
            "save_success": save_success,
            "duration_seconds": round(duration, 2),
            "md_path": str(md_path),
            "metadata_path": str(metadata_path)
        }
        
        if result.success:
            logger.info(f"✅ [{index}/{total}] Success: {file_path.name} ({duration:.2f}s)")
        else:
            logger.error(f"❌ [{index}/{total}] Failed: {file_path.name} ({duration:.2f}s) - {result.error}")
        
        return summary

    def run(self) -> Dict[str, Any]:
        """
        Run the complete file processing pipeline
        
        Returns:
            Dictionary with processing summary
        """
        logger.info("🚀 Starting file extraction process")
        logger.info(f"📁 Input directory: {self.input_dir}")
        logger.info(f"📤 Output directory: {self.output_dir}")
        
        # Discover files
        files = self.discover_files()
        if not files:
            logger.warning("⚠️  No files found to process")
            return {"total_files": 0, "processed": [], "summary": {"success": 0, "failed": 0}}
        
        # Process each file
        processed_files = []
        success_count = 0
        failed_count = 0
        
        for i, file_path in enumerate(files, 1):
            try:
                result = self.process_file(file_path, i, len(files))
                processed_files.append(result)
                
                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error processing {file_path.name}: {e}")
                failed_count += 1
                processed_files.append({
                    "file": file_path.name,
                    "success": False,
                    "extraction_error": str(e),
                    "save_success": False
                })
        
        # Generate summary
        summary = {
            "total_files": len(files),
            "processed": processed_files,
            "summary": {
                "success": success_count,
                "failed": failed_count
            }
        }
        
        logger.info(f"🏁 Processing complete: {success_count} successful, {failed_count} failed")
        return summary

def main():
    """Main function to run the file processor"""
    try:
        # Example configurations:
        # Default: saves to same directory as input files
        # processor = FileProcessor()
        
        # Custom output directory
        # processor = FileProcessor(output_dir="extracted_content")
        
        # Custom input and output directories
        # processor = FileProcessor(input_dir="my_files", output_dir="my_results")
        
        processor = FileProcessor()
        results = processor.run()
        
        # Print final summary
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"   Total files: {results['summary']['success'] + results['summary']['failed']}")
        print(f"   Successful: {results['summary']['success']}")
        print(f"   Failed: {results['summary']['failed']}")
        
        # Save processing log
        log_path = Path("extraction_log.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"   Detailed log: {log_path}")
        
    except KeyboardInterrupt:
        logger.info("⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()