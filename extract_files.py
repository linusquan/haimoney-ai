#!/usr/bin/env python3
"""
Script to extract all files from the hl directory into an output folder
with sequence numbers to prevent name collisions.
"""
import shutil
from pathlib import Path

def extract_files():
    source_dir = Path("/Users/liquan/code/haimoney-ai/hl")
    output_dir = Path("/Users/liquan/code/haimoney-ai/output")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Find all files recursively
    files = []
    for file_path in source_dir.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith('.'):
            files.append(file_path)
    
    # Sort files for consistent ordering
    files.sort()
    
    print(f"Found {len(files)} files to extract")
    
    # Copy files with sequence numbers
    for i, file_path in enumerate(files, 1):
        # Create new filename with sequence number
        new_filename = f"{i:03d}_{file_path.name}"
        destination = output_dir / new_filename
        
        try:
            shutil.copy2(file_path, destination)
            print(f"Copied: {file_path.relative_to(source_dir)} -> {new_filename}")
        except Exception as e:
            print(f"Error copying {file_path}: {e}")
    
    print(f"\nExtraction complete! All files copied to: {output_dir}")

if __name__ == "__main__":
    extract_files()