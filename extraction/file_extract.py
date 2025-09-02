#!/usr/bin/env python3
"""
Single File Extraction Wrapper
Focuses on extracting data from a single file using the existing OpenAI file management code.
"""
import os
import json
import logging
from dataclasses import dataclass
from typing import Optional, TypedDict
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FILE_NUM_LIMIT = 20
DEFAULT_MODEL = 'gpt-4o-mini'

class FileInfo(TypedDict):
    """Type definition for file information object"""
    id: str
    filename: str
    original_path: Optional[str]
    purpose: str
    uploaded_at: str
    size: int
    status: str

@dataclass
class ExtractionResult:
    """Typed response for extraction operations"""
    success: bool
    file_id: Optional[str] = None
    filename: Optional[str] = None
    original_path: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def success_result(cls, result: str, file_id: str, filename: str, original_path: str = None) -> 'ExtractionResult':
        """Create a successful extraction result"""
        return cls(success=True, result=result, file_id=file_id, filename=filename, original_path=original_path)
    
    @classmethod
    def error_result(cls, error: str, file_id: str = None, filename: str = None, original_path: str = None) -> 'ExtractionResult':
        """Create an error extraction result"""
        return cls(success=False, error=error, file_id=file_id, filename=filename, original_path=original_path)

SYSTEM_PROMPT = f"""You are a financial document extraction specialist. Your task is to extract ALL information from the provided document and reproduce it in markdown format while preserving the exact layout, positioning, and structure of the original document. You must output a json structure output in the end with nothing before and after.

**EXTRACTION REQUIREMENTS:**

1. **Exact Value Matching:**
   - Extract all text, numbers, and data EXACTLY as shown in the original
   - Preserve all formatting, spacing, and punctuation
   - Do not summarize, paraphrase, or omit any visible information
   - Include headers, subheaders, labels, and all field values

2. **Layout Preservation:**
   - Use markdown tables, spacing, and line breaks to mirror the document's visual structure
   - Maintain the positional relationship between elements (left/right alignment, spacing)
   - Preserve the hierarchical structure of sections and subsections
   - Keep related information grouped as it appears in the original

3. **Page Handling:**
   - Mark each page transition using: `=== PAGE X OF Y ===`
   - When tables span multiple pages, recreate the table on each new page with the same column headers
   - Maintain continuity of information across page breaks

4. **Markdown Structure:**
   - Use appropriate markdown syntax (headers, tables, lists, emphasis)
   - Ensure tables are properly formatted with aligned columns
   - Use line breaks and spacing to reflect the document's visual hierarchy
5. ***Use notation triple equal with line break for page notation*** 
   - like this example to annotate the page of each document === PAGE 1 OF 2 ===. If there are continuation of table or other structured data you must recreate the heading for the new page.

Your response is a json structure that follows the defined json schema below:
{{
    "type": "json_schema",
    "json_schema": {{
        "name": "extraction_result",
        "schema": {{
            "type": "object",
            "properties": {{
                "result": {{
                    "type": "string",
                    "description": "The extracted content in markdown format"
                }},
                "error": {{
                    "type": "boolean",
                    "description": "If you cannot extract any useful information mark this true"
                }},
                "errorReason": {{
                    "type": "string",
                    "description": "reason of not able to extract"
                }}
            }},
            "required": ["result", "error"],
            "additionalProperties": false
        }}
    }}
}}

Example response

{{
   "result": "payslip: income 123",
   "error": "false"
}}

{{
   "result": "",
   "error": "true"
   "errorReason": "there isn't any information i can extract from this"
}}
"""

class SingleFileExtractor:
    def __init__(self, api_key=None):
        if not api_key:
            load_dotenv()
            api_key = os.getenv("apikey")
            if not api_key:
                raise ValueError("API key not found. Please provide it or set 'apikey' in .env file")
        
        self.api_key = api_key
    
    def extract_from_file_info(self, file_info: FileInfo, extraction_prompt: Optional[str] = None) -> ExtractionResult:
        """
        Extract data from a file using its OpenAI file information.
        
        Args:
            file_info (FileInfo): Typed file information containing id, filename, etc.
            extraction_prompt (str): Custom prompt for extraction
        
        Returns:
            ExtractionResult: Typed response with success status and result/error
        """
        file_id = file_info["id"]
        filename = file_info["filename"]
        original_path = file_info.get("original_path")
        
        if not extraction_prompt:
            extraction_prompt = f"""Extract info form this file"""
        
        logger.info(f"🔍 Extracting data from: {filename}")
        logger.info(f"📄 File ID: {file_id}")
        
        try:
            response = create_chat_completion(
                prompt=extraction_prompt,
                api_key=self.api_key,
                file_ids=[file_id]
            )
            
            if response is None:
                return ExtractionResult.error_result("Failed to get response from OpenAI", file_id, filename, original_path)
            
            # Parse JSON response and extract the result field
            try:
                json_response = json.loads(response)
                extracted_content = json_response.get("result", "")
                return ExtractionResult.success_result(extracted_content, file_id, filename, original_path)
            except json.JSONDecodeError:
                # Fallback: treat as plain text if not valid JSON
                logger.error("failed to extract json from output")
                return ExtractionResult.error_result({"errorReason":  f"failed to parse {response}"}, file_id, filename, original_path)
                
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            return ExtractionResult.error_result(str(e), file_id, filename, original_path)
    
    def extract_with_custom_prompt(self, file_info: FileInfo, custom_prompt: str) -> ExtractionResult:
        """
        Extract data using a custom prompt.
        
        Args:
            file_info (FileInfo): Typed file information
            custom_prompt (str): Custom extraction prompt
            
        Returns:
            ExtractionResult: Typed response with success status and result/error
        """
        return self.extract_from_file_info(file_info, custom_prompt)


def create_chat_completion(prompt, api_key, file_ids=None, model=None):
    """
    Send a chat completion request to OpenAI with structured output
    
    Args:
        prompt (str): The prompt to send
        api_key (str): OpenAI API key (required)
        file_ids (list): List of file IDs to include (optional)
        model (str): Model to use for completion
    
    Returns:
        str: The response content from structured output
    """
    if not api_key:
        raise ValueError("API key is required")
        
    # Use DEFAULT_MODEL as fallback if no model provided
    if not model:
        model = DEFAULT_MODEL
        
    client = OpenAI(api_key=api_key)
    
    try:
        # For file analysis, use the assistants API which supports file attachments
        # Create an assistant with file search capability
        assistant = client.beta.assistants.create(
            name="Document Extractor",
            instructions=SYSTEM_PROMPT,
            model=model,
            tools=[{"type": "file_search"}]
        )
        
        # Create a thread
        thread = client.beta.threads.create()
        
        # Limit to max 10 files (OpenAI limit)
        limited_file_ids = file_ids[:FILE_NUM_LIMIT]
        
        if len(file_ids) > FILE_NUM_LIMIT:
            logger.warning(f"⚠️  Limiting to first 10 files (OpenAI max: 10, you have: {len(file_ids)} files)")

        
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
            attachments=[
                {"file_id": file_id, "tools": [{"type": "file_search"}]}
                for file_id in limited_file_ids
            ],
            
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            return messages.data[0].content[0].text.value
        else:
            return f"Assistant run failed with status: {run.status}"
            
    except Exception as e:
        logger.error(f"❌ Error in chat completion: {str(e)}")
        return None


def main():
    """Example usage with the provided file information"""
    
    # Example file info from the user's request
    example_file_info =  {
      "id": "file-JqesWZfBFrw5RHVFyL1NbL",
      "filename": "008_ResidentialLoan-S212619187201-26Jan2023.pdf",
      "original_path": "output/user_upload/008_ResidentialLoan-S212619187201-26Jan2023.pdf",
      "purpose": "assistants",
      "uploaded_at": "2025-09-02T20:38:20.588754",
      "size": 181418,
      "status": "processed"
    }
    try:
        # Initialize the extractor
        extractor = SingleFileExtractor()
        
        # Extract data from the file
        extraction_result = extractor.extract_from_file_info(example_file_info)
        
        if extraction_result.success:
            print("\n📊 Extraction Results:")
            print("=" * 80)
            print(extraction_result.result)
            print("=" * 80)
        else:
            logger.error(f"❌ Extraction failed: {extraction_result.error}")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()