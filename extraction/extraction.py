#!/usr/bin/env python3
"""
Single File Extraction Wrapper
Focuses on extracting data from a single file using the existing OpenAI file management code.
"""
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gpt-4o-mini'

SYSTEM_PROMPT = f"""You are a financial document extraction specialist. Your task is to extract ALL information from the provided document and reproduce it in markdown format while preserving the exact layout, positioning, and structure of the original document.

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
"""

class SingleFileExtractor:
    def __init__(self, api_key=None):
        if not api_key:
            load_dotenv()
            api_key = os.getenv("apikey")
            if not api_key:
                raise ValueError("API key not found. Please provide it or set 'apikey' in .env file")
        
        self.api_key = api_key
    
    def extract_from_file_info(self, file_info, extraction_prompt=None):
        """
        Extract data from a file using its OpenAI file information.
        
        Args:
            file_info (dict): File information containing id, filename, etc.
            extraction_prompt (str): Custom prompt for extraction
        
        Returns:
            str: Extracted content/analysis from OpenAI
        """
        file_id = file_info["id"]
        filename = file_info["filename"]
        
        if not extraction_prompt:
            extraction_prompt = f"""Extract info form this file"""
        
        logger.info(f"🔍 Extracting data from: {filename}")
        logger.info(f"📄 File ID: {file_id}")
        
        response = create_chat_completion(
            prompt=extraction_prompt,
            api_key=self.api_key,
            file_ids=[file_id]
        )
        
        return response
    
    def extract_with_custom_prompt(self, file_info, custom_prompt):
        """
        Extract data using a custom prompt.
        
        Args:
            file_info (dict): File information
            custom_prompt (str): Custom extraction prompt
            
        Returns:
            str: Extracted content/analysis
        """
        return self.extract_from_file_info(file_info, custom_prompt)


def create_chat_completion(prompt, api_key, file_ids=None, model=None):
    """
    Send a chat completion request to OpenAI
    
    Args:
        prompt (str): The prompt to send
        api_key (str): OpenAI API key (required)
        file_ids (list): List of file IDs to include (optional)
        model (str): Model to use for completion
    
    Returns:
        str: The response content
    """
    if not api_key:
        raise ValueError("API key is required")
        
    # Use DEFAULT_MODEL as fallback if no model provided
    if not model:
        model = DEFAULT_MODEL
        
    client = OpenAI(api_key=api_key)
    
    try:
        # For file analysis, use the assistants API which supports file attachments
        if file_ids:
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
            limited_file_ids = file_ids[:10]
            
            if len(file_ids) > 10:
                logger.warning(f"⚠️  Limiting to first 10 files (OpenAI max: 10, you have: {len(file_ids)} files)")
            
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt,
                attachments=[
                    {"file_id": file_id, "tools": [{"type": "file_search"}]}
                    for file_id in limited_file_ids
                ]
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
        else:
            # Fallback to regular chat completion without files
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"❌ Error in chat completion: {str(e)}")
        return None


def main():
    """Example usage with the provided file information"""
    
    # Example file info from the user's request
    example_file_info = {
        "id": "file-JgksmaesdMEJgYQPB7YUUE",
        "filename": "002_TransactionSummary 2.pdf",
        "original_path": "/Users/liquan/code/haimoney-ai/output/002_TransactionSummary 2.pdf",
        "purpose": "assistants",
        "uploaded_at": "2025-09-02T07:33:59.305759",
        "size": 447422,
        "status": "processed"
    }
    
    try:
        # Initialize the extractor
        extractor = SingleFileExtractor()
        
        # Extract data from the file
        result = extractor.extract_from_file_info(example_file_info)
        
        if result:
            print("\n📊 Extraction Results:")
            print("=" * 80)
            print(result)
            print("=" * 80)
        else:
            logger.error("❌ Extraction failed")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()