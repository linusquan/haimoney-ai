#!/usr/bin/env python3
"""
Folder Extraction Script
Reads file_upload_meta.json and processes all files through extract_upload,
saving individual extraction results to output/extraction folder
and creating a summary extract_meta.json file.
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from file_extract import SingleFileExtractor

# Configure logging - suppress external library logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

# Set external library log levels to WARNING to reduce noise
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class FolderExtractor:
    def __init__(self, meta_file_path: str, output_dir: str):
        """
        Initialize folder extractor with metadata file path and output directory.
        
        Args:
            meta_file_path: Path to file_upload_meta.json
            output_dir: Directory to save extraction results
        """
        self.meta_file_path = meta_file_path
        self.output_dir = Path(output_dir)
        self.extractor = SingleFileExtractor()
        self.extraction_results = []
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_metadata(self) -> Dict[str, Any]:
        """Load file upload metadata from JSON file."""
        try:
            with open(self.meta_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Metadata file not found: {self.meta_file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in metadata file: {e}")
            raise
            
    def extract_all_files(self) -> List[Dict[str, Any]]:
        """
        Extract content from all files listed in metadata.
        
        Returns:
            List of extraction results with metadata
        """
        logger.info("= Starting folder extraction process...")
        
        # Load metadata
        metadata = self.load_metadata()
        files = metadata.get("files", [])
        
        if not files:
            logger.warning("No files found in metadata")
            return []
            
        logger.info(f"=Found {len(files)} files to process")
        
        extraction_results = []
        
        for i, file_info in enumerate(files, 1):
            logger.info(f"= Processing file {i}/{len(files)}: {file_info['filename']}")
            
            try:
                # Extract content using SingleFileExtractor
                result = self.extractor.extract_from_file_info(file_info)
                
                if result.success:
                    # Save individual extraction to file
                    output_filename = self._get_output_filename(file_info['filename'])
                    output_path = self.output_dir / output_filename
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result.result)
                    
                    logger.info(f" Successfully extracted to: {output_path}")
                    
                    # Add to results list
                    extraction_info = {
                        "file_id": result.file_id,
                        "original_filename": result.filename,
                        "original_path": result.original_path,
                        "extraction_filename": output_filename,
                        "extraction_path": str(output_path),
                        "status": "success",
                        "extracted_at": datetime.now().isoformat(),
                        "file_size": file_info.get('size', 0)
                    }
                    extraction_results.append(extraction_info)
                    
                    # Update metadata immediately after each successful extraction
                    self.extraction_results = extraction_results
                    self._update_extraction_metadata()
                    
                else:
                    logger.error(f"L Failed to extract {file_info['filename']}: {result.error}")
                    
                    # Add error to results list
                    extraction_info = {
                        "file_id": result.file_id or file_info['id'],
                        "original_filename": result.filename or file_info['filename'],
                        "original_path": result.original_path or file_info.get('original_path'),
                        "extraction_filename": None,
                        "extraction_path": None,
                        "status": "failed",
                        "error": result.error,
                        "extracted_at": datetime.now().isoformat(),
                        "file_size": file_info.get('size', 0)
                    }
                extraction_results.append(extraction_info)
                
                # Update metadata immediately after each failed extraction  
                self.extraction_results = extraction_results
                self._update_extraction_metadata()
                
            except Exception as e:
                logger.error(f"L Unexpected error processing {file_info['filename']}: {str(e)}")
                
                # Add error to results list
                extraction_info = {
                    "file_id": file_info['id'],
                    "original_filename": file_info['filename'],
                    "original_path": file_info.get('original_path'),
                    "extraction_filename": None,
                    "extraction_path": None,
                    "status": "failed",
                    "error": str(e),
                    "extracted_at": datetime.now().isoformat(),
                    "file_size": file_info.get('size', 0)
                }
                extraction_results.append(extraction_info)
                
                # Update metadata immediately after each unexpected error
                self.extraction_results = extraction_results
                self._update_extraction_metadata()
        
        self.extraction_results = extraction_results
        return extraction_results
    
    def _get_output_filename(self, original_filename: str) -> str:
        """
        Generate output filename for extraction result.
        
        Args:
            original_filename: Original file name
            
        Returns:
            Generated filename with .md extension
        """
        # Remove extension and add .md
        base_name = Path(original_filename).stem
        return f"{base_name}_extraction.md"
    
    def _update_extraction_metadata(self) -> None:
        """
        Update extraction metadata file after each extraction.
        This provides real-time progress tracking.
        """
        if not self.extraction_results:
            return
            
        metadata_path = self.output_dir / "extract_meta.json"
        
        # Create summary metadata
        successful_extractions = [r for r in self.extraction_results if r['status'] == 'success']
        failed_extractions = [r for r in self.extraction_results if r['status'] == 'failed']
        
        summary_metadata = {
            "extraction_summary": {
                "total_files": len(self.extraction_results),
                "successful_extractions": len(successful_extractions),
                "failed_extractions": len(failed_extractions),
                "last_updated": datetime.now().isoformat(),
                "output_directory": str(self.output_dir)
            },
            "extracted_files": successful_extractions,
            "failed_files": failed_extractions
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(summary_metadata, f, indent=2, ensure_ascii=False)
    
    def save_extraction_metadata(self) -> str:
        """
        Save extraction metadata to extract_meta.json.
        
        Returns:
            Path to the saved metadata file
        """
        if not self.extraction_results:
            logger.warning("No extraction results to save")
            return None
            
        metadata_path = self.output_dir / "extract_meta.json"
        
        # Create summary metadata
        successful_extractions = [r for r in self.extraction_results if r['status'] == 'success']
        failed_extractions = [r for r in self.extraction_results if r['status'] == 'failed']
        
        summary_metadata = {
            "extraction_summary": {
                "total_files": len(self.extraction_results),
                "successful_extractions": len(successful_extractions),
                "failed_extractions": len(failed_extractions),
                "extraction_date": datetime.now().isoformat(),
                "output_directory": str(self.output_dir)
            },
            "extracted_files": successful_extractions,
            "failed_files": failed_extractions
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(summary_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"=Extraction metadata saved to: {metadata_path}")
        logger.info(f" Successful: {len(successful_extractions)}, L Failed: {len(failed_extractions)}")
        
        return str(metadata_path)
    
    def run_extraction(self) -> Dict[str, Any]:
        """
        Run the complete extraction process.
        
        Returns:
            Summary of extraction process
        """
        logger.info("<� Starting complete folder extraction process...")
        
        # Extract all files
        results = self.extract_all_files()
        
        # Save metadata
        metadata_path = self.save_extraction_metadata()
        
        # Return summary
        successful_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        
        summary = {
            "total_files": len(results),
            "successful_extractions": successful_count,
            "failed_extractions": failed_count,
            "output_directory": str(self.output_dir),
            "metadata_file": metadata_path,
            "completion_time": datetime.now().isoformat()
        }
        
        logger.info("<Extraction process completed!")
        logger.info(f"=Results: {successful_count} successful, {failed_count} failed out of {len(results)} total files")
        
        return summary


def main():
    """Main function to run folder extraction."""
    
    # Configuration
    meta_file_path = "/Users/liquan/code/haimoney-ai/output/file_upload_meta.json"
    output_dir = "/Users/liquan/code/haimoney-ai/output/extraction"
    
    try:
        # Initialize folder extractor
        folder_extractor = FolderExtractor(meta_file_path, output_dir)
        
        # Run extraction process
        summary = folder_extractor.run_extraction()
        
        print("\n" + "="*60)
        print("=� EXTRACTION COMPLETE")
        print("="*60)
        print(f"Total Files Processed: {summary['total_files']}")
        print(f"Successful Extractions: {summary['successful_extractions']}")
        print(f"Failed Extractions: {summary['failed_extractions']}")
        print(f"Output Directory: {summary['output_directory']}")
        print(f"Metadata File: {summary['metadata_file']}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"L Fatal error during extraction: {str(e)}")
        raise


if __name__ == "__main__":
    main()