#!/usr/bin/env python3
"""
OpenAI File Upload and Chat Completion Script
Uploads files to OpenAI, sends chat completion requests, and manages file IDs.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

MODEL='gpt-4o-mini'

class OpenAIFileManager:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.file_ids_file = "openai_uploaded_files.json"
        self.uploaded_files = self.load_file_ids()
    
    def load_file_ids(self):
        """Load previously uploaded file IDs from JSON file"""
        if os.path.exists(self.file_ids_file):
            with open(self.file_ids_file, 'r') as f:
                return json.load(f)
        return {"files": [], "upload_sessions": []}
    
    def save_file_ids(self):
        """Save uploaded file IDs to JSON file"""
        with open(self.file_ids_file, 'w') as f:
            json.dump(self.uploaded_files, f, indent=2)
    
    def upload_file(self, file_path, purpose="assistants"):
        """
        Upload a file to OpenAI
        
        Args:
            file_path (str): Path to the file to upload
            purpose (str): Purpose of the file ('assistants', 'fine-tune', etc.)
        
        Returns:
            dict: File object with id, filename, etc.
        """
        try:
            with open(file_path, "rb") as file:
                response = self.client.files.create(
                    file=file,
                    purpose=purpose
                )
                
                # Store file info
                file_info = {
                    "id": response.id,
                    "filename": os.path.basename(file_path),
                    "original_path": str(file_path),
                    "purpose": purpose,
                    "uploaded_at": datetime.now().isoformat(),
                    "size": response.bytes,
                    "status": response.status
                }
                
                self.uploaded_files["files"].append(file_info)
                self.save_file_ids()
                
                print(f"✅ Uploaded: {file_info['filename']} -> File ID: {response.id}")
                return response
                
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {str(e)}")
            return None
    
    def upload_directory(self, directory_path, purpose="assistants"):
        """Upload all files in a directory"""
        directory = Path(directory_path)
        uploaded_files = []
        
        if not directory.exists():
            print(f"❌ Directory not found: {directory_path}")
            return uploaded_files
        
        print(f"📁 Uploading files from: {directory_path}")
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                result = self.upload_file(str(file_path), purpose)
                if result:
                    uploaded_files.append(result)
        
        # Save session info
        session_info = {
            "directory": str(directory_path),
            "uploaded_at": datetime.now().isoformat(),
            "file_count": len(uploaded_files),
            "file_ids": [f.id for f in uploaded_files]
        }
        self.uploaded_files["upload_sessions"].append(session_info)
        self.save_file_ids()
        
        print(f"📊 Upload complete: {len(uploaded_files)} files uploaded")
        return uploaded_files
    
    def get_all_file_ids(self):
        """Get all uploaded file IDs"""
        return [file_info["id"] for file_info in self.uploaded_files["files"]]

def main():
    # Load environment variables
    load_dotenv()
    # Get API key from environment variable
    API_KEY = os.getenv("apikey")
    if not API_KEY:
        print("❌ Error: API key not found in .env file")
        print("Please add 'apikey=your-openai-api-key-here' to your .env file")
        return
    
    # Initialize file manager
    manager = OpenAIFileManager(API_KEY)
    
    # Check if files are already uploaded
    existing_file_ids = manager.get_all_file_ids()
    
    if existing_file_ids:
        print(f"📁 Found {len(existing_file_ids)} already uploaded files, skipping upload")
        file_ids = existing_file_ids
        uploaded_files = True  # Set to True to continue with chat completion
    else:
        # Upload files from the output directory
        output_dir = "./output"
        if os.path.exists(output_dir):
            uploaded_files = manager.upload_directory(output_dir)
            
            if uploaded_files:
                # Get all uploaded file IDs
                file_ids = [f.id for f in uploaded_files]
            else:
                uploaded_files = None
                file_ids = []
        else:
            print(f"❌ Output directory not found: {output_dir}")
            print("Please run the file extraction script first or specify a different directory")
            return
        print(f"\n💾 File IDs saved to: {manager.file_ids_file}")
        print("Use cleanup_openai_files.py to delete these files after testing")


if __name__ == "__main__":
    main()