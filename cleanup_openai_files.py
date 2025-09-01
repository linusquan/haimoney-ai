#!/usr/bin/env python3
"""
OpenAI File Cleanup Script
Deletes all uploaded files from OpenAI based on stored file IDs.
"""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

class OpenAIFileCleanup:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.file_ids_file = "openai_uploaded_files.json"
    
    def load_file_ids(self):
        """Load file IDs from JSON file"""
        if not os.path.exists(self.file_ids_file):
            print(f"❌ File not found: {self.file_ids_file}")
            return {"files": [], "upload_sessions": []}
        
        with open(self.file_ids_file, 'r') as f:
            return json.load(f)
    
    def delete_file(self, file_id, filename=None):
        """Delete a single file from OpenAI"""
        try:
            response = self.client.files.delete(file_id)
            if response.deleted:
                print(f"✅ Deleted: {filename or file_id}")
                return True
            else:
                print(f"❌ Failed to delete: {filename or file_id}")
                return False
        except Exception as e:
            print(f"❌ Error deleting {filename or file_id}: {str(e)}")
            return False
    
    def delete_all_files(self, confirm=True):
        """Delete all uploaded files"""
        data = self.load_file_ids()
        files = data.get("files", [])
        
        if not files:
            print("📭 No files to delete")
            return
        
        print(f"📋 Found {len(files)} files to delete:")
        for file_info in files:
            print(f"  - {file_info['filename']} (ID: {file_info['id']})")
        
        if confirm:
            response = input(f"\n⚠️  Are you sure you want to delete {len(files)} files? (y/N): ")
            if response.lower() != 'y':
                print("🚫 Deletion cancelled")
                return
        
        print("\n🗑️  Starting file deletion...")
        deleted_count = 0
        failed_count = 0
        
        for file_info in files:
            if self.delete_file(file_info['id'], file_info['filename']):
                deleted_count += 1
            else:
                failed_count += 1
        
        print(f"\n📊 Deletion Summary:")
        print(f"  ✅ Successfully deleted: {deleted_count}")
        print(f"  ❌ Failed to delete: {failed_count}")
        
        if deleted_count > 0:
            # Clear the JSON file after successful deletions
            self.clear_file_records()
    
    def delete_by_session(self, session_index=None):
        """Delete files from a specific upload session"""
        data = self.load_file_ids()
        sessions = data.get("upload_sessions", [])
        
        if not sessions:
            print("📭 No upload sessions found")
            return
        
        if session_index is None:
            print("📋 Available upload sessions:")
            for i, session in enumerate(sessions):
                print(f"  {i}: {session['directory']} - {session['file_count']} files ({session['uploaded_at']})")
            
            try:
                session_index = int(input("Enter session number to delete: "))
            except (ValueError, IndexError):
                print("❌ Invalid session number")
                return
        
        if session_index < 0 or session_index >= len(sessions):
            print("❌ Invalid session number")
            return
        
        session = sessions[session_index]
        file_ids = session['file_ids']
        
        print(f"\n🗑️  Deleting {len(file_ids)} files from session: {session['directory']}")
        
        deleted_count = 0
        for file_id in file_ids:
            if self.delete_file(file_id):
                deleted_count += 1
        
        print(f"✅ Deleted {deleted_count}/{len(file_ids)} files from session")
    
    def clear_file_records(self):
        """Clear the JSON file records"""
        empty_data = {"files": [], "upload_sessions": []}
        with open(self.file_ids_file, 'w') as f:
            json.dump(empty_data, f, indent=2)
        print(f"🧹 Cleared file records from {self.file_ids_file}")
    
    def list_remote_files(self):
        """List all files in your OpenAI account"""
        try:
            files = self.client.files.list()
            print("\n📋 All files in your OpenAI account:")
            print("-" * 80)
            
            for file in files.data:
                print(f"ID: {file.id}")
                print(f"Filename: {file.filename}")
                print(f"Purpose: {file.purpose}")
                print(f"Size: {file.bytes} bytes")
                print(f"Created: {file.created_at}")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ Error listing files: {str(e)}")


def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment variable
    API_KEY = os.getenv("apikey")
    if not API_KEY:
        print("❌ Error: API key not found in .env file")
        print("Please add 'apikey=your-openai-api-key-here' to your .env file")
        return
    
    cleanup = OpenAIFileCleanup(API_KEY)
    
    print("🧹 OpenAI File Cleanup Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Delete all uploaded files")
        print("2. Delete files by upload session")
        print("3. List local file records")
        print("4. List all remote files")
        print("5. Clear local file records only")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            cleanup.delete_all_files()
        elif choice == '2':
            cleanup.delete_by_session()
        elif choice == '3':
            data = cleanup.load_file_ids()
            files = data.get("files", [])
            print(f"\n📋 Local file records ({len(files)} files):")
            for file_info in files:
                print(f"  - {file_info['filename']} (ID: {file_info['id']})")
        elif choice == '4':
            cleanup.list_remote_files()
        elif choice == '5':
            cleanup.clear_file_records()
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")


if __name__ == "__main__":
    main()