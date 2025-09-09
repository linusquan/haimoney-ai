#!/usr/bin/env python3
"""
Gemini File Extraction Wrapper
Extracts data from files (documents and images) using Google's Gemini AI API with structured output.
"""
import os
import logging
import mimetypes
from dataclasses import dataclass
from typing import Optional, TypedDict
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel
from PIL import Image
logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gemini-2.5-flash'

def _load_system_prompt() -> str:
    """Load the system prompt from external file"""
    try:
        prompt_path = Path(__file__).parent / "system_prompt.txt"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"❌ System prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"System prompt file not found: {prompt_path}")
    except Exception as e:
        logger.error(f"❌ Error loading system prompt: {e}")
        raise

# Load system prompt at module import
SYSTEM_PROMPT = _load_system_prompt()

class ExtractionResponse(BaseModel):
    """Pydantic model for structured extraction response"""
    result: str
    description: str
    error: bool
    errorReason: str

class FileInfo(TypedDict):
    """Type definition for file information object"""
    file_path: str
    filename: str
    mime_type: str
    size: int
    file_type: str

@dataclass
class ExtractionResult:
    """Typed response for extraction operations"""
    success: bool
    file_path: Optional[str] = None
    filename: Optional[str] = None
    result: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def success_result(cls, result: str, description: str, file_path: str, filename: str) -> 'ExtractionResult':
        """Create a successful extraction result"""
        return cls(success=True, result=result, description=description, 
                  file_path=file_path, filename=filename)
    
    @classmethod
    def error_result(cls, error: str, file_path: str = None, filename: str = None) -> 'ExtractionResult':
        """Create an error extraction result"""
        return cls(success=False, error=error, file_path=file_path, filename=filename)


class GeminiFileExtractor:
    def __init__(self, api_key=None):
        """
        Initialize the Gemini File Extractor
        
        Args:
            api_key (str): Google AI API key. If not provided, will look for GOOGLE_AI_API_KEY in .env
        """
        if not api_key:
            load_dotenv()
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if not api_key:
                raise ValueError("Google AI API key not found. Please provide it or set 'GOOGLE_AI_API_KEY' in .env file")
        
        # Configure the API key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)
        logger.info(f"✅ Initialized Gemini File Extractor with model: {DEFAULT_MODEL}")
    
    def _get_file_info(self, file_path: str) -> FileInfo:
        """
        Get file information including mime type and file type
        Only supports PDF documents and image files (JPG, PNG, GIF, BMP, WEBP)
        
        Args:
            file_path (str): Path to the file
        
        Returns:
            FileInfo: File information dictionary
        
        Raises:
            ValueError: If file type is not supported
        """
        path = Path(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Check file extension for supported types
        ext = path.suffix.lower()
        
        # Supported image formats
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            file_type = 'image'
            if ext == '.jpg':
                mime_type = 'image/jpeg'
            elif ext == '.jpeg':
                mime_type = 'image/jpeg'
            else:
                mime_type = f'image/{ext[1:]}'
        
        # Supported document formats (PDF only)
        elif ext == '.pdf':
            file_type = 'document'
            mime_type = 'application/pdf'
        
        # Unsupported file type
        else:
            supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            raise ValueError(f"Unsupported file type: {ext}. Supported formats: {', '.join(supported_formats)}")
        
        return FileInfo(
            file_path=file_path,
            filename=path.name,
            mime_type=mime_type,
            size=path.stat().st_size if path.exists() else 0,
            file_type=file_type
        )
    
    def extract_from_file(self, file_path: str, extraction_prompt: Optional[str] = None) -> ExtractionResult:
        """
        Extract data from a file (document or image) using Gemini AI
        
        Args:
            file_path (str): Path to the file to extract data from
            extraction_prompt (str): Custom prompt for extraction
        
        Returns:
            ExtractionResult: Typed response with success status and result/error
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return ExtractionResult.error_result(f"File not found: {file_path}", file_path)
            
            # Get file information (will raise ValueError for unsupported types)
            try:
                file_info = self._get_file_info(file_path)
            except ValueError as ve:
                return ExtractionResult.error_result(str(ve), file_path, Path(file_path).name)
            
            if not extraction_prompt:
                extraction_prompt = "Extract all information from this file"
            
            logger.info(f"🔍 Extracting data from: {file_info['filename']} ({file_info['file_type']})")
            logger.info(f"📄 File path: {file_path}")
            logger.info(f"📊 MIME type: {file_info['mime_type']}")
            
            # Prepare content based on file type
            if file_info['file_type'] == 'image':
                # Load image for image files
                image = Image.open(file_path)
                content = [f"{SYSTEM_PROMPT}\n\n{extraction_prompt}", image]
            else:
                # Upload document file for processing
                uploaded_file = genai.upload_file(path=file_path, mime_type=file_info['mime_type'])
                content = [f"{SYSTEM_PROMPT}\n\n{extraction_prompt}", uploaded_file]
            
            # Configure for structured output
            generation_config = genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ExtractionResponse
            )
            
            # Generate structured content
            response = self.model.generate_content(
                content,
                generation_config=generation_config
            )
            
            # Parse the structured response
            try:
                # Parse the JSON response manually first to handle missing fields
                import json
                json_data = json.loads(response.text)
                # Now create the response object
                extraction_response = ExtractionResponse.model_validate(json_data)
                
                # Check if extraction was successful
                if extraction_response.error:
                    error_reason = extraction_response.errorReason or "Unknown extraction error"
                    return ExtractionResult.error_result(error_reason, file_path, file_info['filename'])
                else:
                    return ExtractionResult.success_result(
                        result=extraction_response.result,
                        description=extraction_response.description,
                        file_path=file_path,
                        filename=file_info['filename']
                    )
            except Exception as parse_error:
                logger.error(f"❌ Failed to parse structured response: {str(parse_error)}")
                logger.error(f"Raw response: {response.text}")
                return ExtractionResult.error_result(f"Response parsing error: {str(parse_error)}", file_path, file_info['filename'])
                
        except Exception as e:
            logger.error(f"❌ Error during extraction: {str(e)}")
            return ExtractionResult.error_result(str(e), file_path, Path(file_path).name if file_path else None)
    
    def extract_with_custom_prompt(self, file_path: str, custom_prompt: str) -> ExtractionResult:
        """
        Extract data using a custom prompt
        
        Args:
            file_path (str): Path to the file
            custom_prompt (str): Custom extraction prompt
            
        Returns:
            ExtractionResult: Typed response with success status and result/error
        """
        return self.extract_from_file(file_path, custom_prompt)

def main():
    """Simple demo of the extractor - use test_extraction.py for comprehensive testing"""
    print("Gemini File Extractor Demo")
    print("For comprehensive testing, run: python test_extraction.py")
    print("Supported formats: PDF, JPG, JPEG, PNG, GIF, BMP, WEBP")

if __name__ == "__main__":
    main()