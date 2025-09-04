#!/usr/bin/env python3
"""
Fact Find Script
Combines extracted .md files with their metadata JSON files from output/extraction directory
and formats them in a structured XML-like output format.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FactFinder:
    def __init__(self, extraction_dir: str = "output/extraction"):
        """
        Initialize the FactFinder
        
        Args:
            extraction_dir: Directory containing extracted .md and metadata JSON files
        """
        self.extraction_dir = Path(extraction_dir)
        
        if not self.extraction_dir.exists():
            raise FileNotFoundError(f"Extraction directory not found: {self.extraction_dir}")
    
    def discover_md_files(self) -> List[Path]:
        """
        Discover all .md files in the extraction directory
        
        Returns:
            List of .md file paths
        """
        md_files = []
        for file_path in self.extraction_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.md':
                md_files.append(file_path)
        
        logger.info(f"📁 Discovered {len(md_files)} .md files")
        return sorted(md_files)
    
    def get_metadata_path(self, md_file: Path) -> Path:
        """
        Get the corresponding metadata JSON file path for a .md file
        
        Args:
            md_file: Path to the .md file
            
        Returns:
            Path to the metadata JSON file
        """
        base_name = md_file.stem
        metadata_file = md_file.parent / f"{base_name}-hmoney-metadata.json"
        return metadata_file
    
    def load_metadata(self, metadata_path: Path) -> Dict:
        """
        Load metadata from JSON file
        
        Args:
            metadata_path: Path to metadata JSON file
            
        Returns:
            Dictionary containing metadata, or error info if failed
        """
        try:
            if not metadata_path.exists():
                return {
                    "filename": metadata_path.stem.replace("-hmoney-metadata", ""),
                    "description": "Metadata file not found",
                    "error": True,
                    "errorReason": f"Metadata file not found: {metadata_path.name}"
                }
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata
                
        except Exception as e:
            logger.error(f"❌ Error loading metadata from {metadata_path.name}: {e}")
            return {
                "filename": metadata_path.stem.replace("-hmoney-metadata", ""),
                "description": "Error loading metadata",
                "error": True,
                "errorReason": str(e)
            }
    
    def load_md_content(self, md_path: Path) -> str:
        """
        Load content from .md file
        
        Args:
            md_path: Path to .md file
            
        Returns:
            String content of the file
        """
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"❌ Error loading content from {md_path.name}: {e}")
            return f"Error loading file content: {e}"
    
    def format_file_output(self, md_file: Path, metadata: Dict, content: str) -> str:
        """
        Format a single file's output in the specified XML-like format
        
        Args:
            md_file: Path to the .md file
            metadata: Metadata dictionary
            content: File content
            
        Returns:
            Formatted output string
        """
        # Format metadata as pretty JSON
        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        
        output = f"""<file>
<meta>
{metadata_json}
</meta>
<body>
{content}
</body>
end of {md_file.name}
</file>"""
        
        return output
    
    def combine_files(self) -> str:
        """
        Combine all .md files with their metadata into the specified format
        
        Returns:
            Combined output string
        """
        logger.info("🔍 Starting fact finding process")
        
        # Discover all .md files
        md_files = self.discover_md_files()
        
        if not md_files:
            logger.warning("⚠️  No .md files found")
            return "No .md files found in the extraction directory."
        
        combined_output = []
        success_count = 0
        error_count = 0
        
        # Process each .md file
        for i, md_file in enumerate(md_files, 1):
            logger.info(f"📄 [{i}/{len(md_files)}] Processing: {md_file.name}")
            
            try:
                # Get metadata path and load metadata
                metadata_path = self.get_metadata_path(md_file)
                metadata = self.load_metadata(metadata_path)
                
                # Load .md content
                content = self.load_md_content(md_file)
                
                # Format output
                formatted_output = self.format_file_output(md_file, metadata, content)
                combined_output.append(formatted_output)
                
                if metadata.get("error", False):
                    error_count += 1
                    logger.warning(f"⚠️  [{i}/{len(md_files)}] {md_file.name} - {metadata.get('errorReason', 'Unknown error')}")
                else:
                    success_count += 1
                    logger.info(f"✅ [{i}/{len(md_files)}] Successfully processed: {md_file.name}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ [{i}/{len(md_files)}] Error processing {md_file.name}: {e}")
                
                # Add error entry
                error_metadata = {
                    "filename": md_file.name,
                    "description": "Processing error",
                    "error": True,
                    "errorReason": str(e)
                }
                error_output = self.format_file_output(md_file, error_metadata, f"Error processing file: {e}")
                combined_output.append(error_output)
        
        # Join all outputs
        final_output = "\n\n".join(combined_output)
        
        logger.info(f"🏁 Fact finding complete: {success_count} successful, {error_count} errors")
        return final_output
    
    def save_combined_output(self, output: str, output_file: str = "factfind_combined.txt") -> bool:
        """
        Save the combined output to a file
        
        Args:
            output: Combined output string
            output_file: Output file name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            logger.info(f"💾 Combined output saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving output to {output_file}: {e}")
            return False

def main():
    """Main function to run the fact finder"""
    try:
        # Initialize fact finder
        fact_finder = FactFinder()
        
        # Combine all files
        combined_output = fact_finder.combine_files()
        
        # Print combined output
        print(combined_output)
        
        # Optionally save to file
        fact_finder.save_combined_output(combined_output)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())