# OpenAI File Upload and Management Scripts

This repository contains Python scripts for uploading files to OpenAI, sending chat completion requests, and managing uploaded files.

## Scripts Overview

### 1. `openai_file_manager.py`
Main script that:
- Uploads files from a directory to OpenAI
- Sends chat completion requests with uploaded files
- Saves file IDs to `openai_uploaded_files.json`
- Provides file management capabilities

### 2. `cleanup_openai_files.py`
Cleanup script that:
- Deletes uploaded files from OpenAI
- Manages files by upload session
- Provides interactive cleanup interface
- Clears local file records

### 3. `extract_files.py`
Utility script that:
- Extracts all files from nested directories
- Prevents name collisions with sequence numbering
- Copies files to an `output` folder

## Setup

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key in both scripts:
   - Edit `openai_file_manager.py` and replace `"your-openai-api-key-here"`
   - Edit `cleanup_openai_files.py` and replace `"your-openai-api-key-here"`

## Usage

### Step 1: Extract Files (Optional)
If you have nested directories with files, first extract them:
```bash
python3 extract_files.py
```

### Step 2: Upload Files and Get Chat Completion
```bash
python3 openai_file_manager.py
```

This will:
- Upload all files from the `output` directory
- Send a chat completion request analyzing the files
- Save file IDs to `openai_uploaded_files.json`

### Step 3: Cleanup After Testing
```bash
python3 cleanup_openai_files.py
```

Choose from the interactive menu:
1. Delete all uploaded files
2. Delete files by upload session
3. List local file records
4. List all remote files
5. Clear local file records only
6. Exit

## File Management

### File ID Storage
File IDs are stored in `openai_uploaded_files.json` with structure:
```json
{
  "files": [
    {
      "id": "file-xyz123",
      "filename": "document.pdf",
      "original_path": "/path/to/original/document.pdf",
      "purpose": "assistants",
      "uploaded_at": "2024-01-01T12:00:00.000000",
      "size": 12345,
      "status": "processed"
    }
  ],
  "upload_sessions": [
    {
      "directory": "/path/to/upload/directory",
      "uploaded_at": "2024-01-01T12:00:00.000000",
      "file_count": 5,
      "file_ids": ["file-xyz123", "file-abc456"]
    }
  ]
}
```

### Supported File Types
OpenAI supports various file types including:
- PDF documents
- Text files
- Images (PNG, JPEG, etc.)
- Office documents
- Code files

Check the [OpenAI documentation](https://platform.openai.com/docs/api-reference/files) for the complete list.

## Security Notes

⚠️ **Important**: 
- Never commit API keys to version control
- Use environment variables for production
- These scripts are for POC/testing purposes only
- Always clean up test files to avoid charges

## Error Handling

The scripts include comprehensive error handling for:
- File upload failures
- API request failures
- Missing files or directories
- Invalid file formats
- Network connectivity issues

## API Limits

Be aware of OpenAI's:
- File size limits (512MB per file)
- Total storage limits
- Rate limiting
- Billing for file storage and processing