#!/usr/bin/env python3
"""
Gemini File Extraction Wrapper
Extracts data from files (documents and images) using Google's Gemini AI API with structured output.
"""
import os
import json
import logging
import mimetypes
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from dataclasses import dataclass
from typing import Optional, TypedDict, List
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel
from PIL import Image
from tools.file_extract.system_prompt import SYSTEM_PROMPT
from tools.llm_json_parser import LLMJSONParser
logger = logging.getLogger(__name__)
DEFAULT_MODEL = 'gemini-2.5-flash'

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
    def __init__(self, api_key=None, gemini_model=DEFAULT_MODEL, enable_llm_json_fallback=True):
        """
        Initialize the Gemini File Extractor

        Args:
            api_key (str): Google AI API key. If not provided, will look for GOOGLE_AI_API_KEY in .env
            gemini_model (str): Gemini model to use for extraction
            enable_llm_json_fallback (bool): Whether to use LLM JSON parser as fallback for invalid JSON
        """
        if not api_key:
            load_dotenv()
            api_key = os.getenv("GOOGLE_AI_API_KEY")
            if not api_key:
                raise ValueError("Google AI API key not found. Please provide it or set 'GOOGLE_AI_API_KEY' in .env file")

        # Configure the API key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(gemini_model)
        self.system_prompt = self._load_system_prompt()

        # Initialize LLM JSON parser for fallback if enabled
        self.llm_json_parser = None
        self.enable_llm_json_fallback = enable_llm_json_fallback
        if enable_llm_json_fallback:
            try:
                self.llm_json_parser = LLMJSONParser()
                logger.info("LLM JSON parser initialized for fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM JSON parser: {e}")
                self.enable_llm_json_fallback = False

        logger.info(f"Initialized Gemini File Extractor with model: {gemini_model}")
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from system_prompt.py"""
        try:
            return SYSTEM_PROMPT.strip()
        except ImportError as e:
            logger.error(f"Could not import system prompt: {e}")
            raise ImportError(f"Could not import system prompt from system_prompt.py: {e}")
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            raise

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
            
            logger.info(f"Extracting data from: {file_info['filename']} ({file_info['file_type']})")
            logger.info(f"File path: {file_path}")
            logger.info(f"MIME type: {file_info['mime_type']}")
            
            # Prepare content based on file type
            uploaded_file = None
            try:
                if file_info['file_type'] == 'image':
                    # Load image for image files
                    with Image.open(file_path) as image:
                        # Convert to RGB if necessary to avoid issues with different formats
                        if image.mode in ('RGBA', 'LA', 'P'):
                            image = image.convert('RGB')
                        content = [f"{self.system_prompt}\n\n{extraction_prompt}", image.copy()]
                else:
                    # Upload document file for processing
                    uploaded_file = genai.upload_file(path=file_path, mime_type=file_info['mime_type'])
                    content = [f"{self.system_prompt}\n\n{extraction_prompt}", uploaded_file]
            
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

                    # Strip markdown code blocks if present using regex
                    import re
                    response_text = response.text.strip()

                    # Match and extract JSON from code blocks with optional line breaks
                    code_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                    if code_block_match:
                        response_text = code_block_match.group(1).strip()
                    else:
                        # If no code block found, use original text
                        response_text = response_text
                    json_data = json.loads(response_text)
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
                    # sometimes the extraction fails due to the response contains: ```{json_content}```
                    logger.warning(f"Initial JSON parsing failed: {str(parse_error)}")

                    # Try LLM JSON parser as fallback
                    if self.enable_llm_json_fallback and self.llm_json_parser:
                        logger.info("Attempting LLM JSON parser fallback...")
                        try:
                            # Create a properly structured JSON string for the LLM to fix
                            # The issue is usually with the 'result' field containing problematic content
                            fallback_json = f'{{"description": "Extracted content", "error": false, "errorReason": "", "result": {json.dumps(response_text)}}}'

                            llm_result = self.llm_json_parser.fix_json_string(fallback_json)

                            if llm_result.success:
                                logger.info("LLM JSON parser successfully fixed the response")

                                # Create extraction response from fixed JSON
                                extraction_response = ExtractionResponse.model_validate(llm_result.parsed_json)

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
                            else:
                                logger.error(f"LLM JSON parser also failed: {llm_result.error}")

                        except Exception as llm_error:
                            logger.error(f"LLM JSON parser encountered error: {str(llm_error)}")

                    # Both initial parsing and LLM fallback failed
                    logger.error(f"All JSON parsing attempts failed. Raw response: {response.text}")
                    return ExtractionResult.error_result(f"Response parsing error: {str(parse_error)}", file_path, file_info['filename'])

            finally:
                # Clean up uploaded file to prevent resource leaks
                if uploaded_file:
                    try:
                        genai.delete_file(uploaded_file.name)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup uploaded file: {cleanup_error}")
                
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
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

    def extract_multiple_files(
        self,
        file_paths: List[str],
        max_concurrent: int = 5,
        timeout_seconds: int = 240,
        extraction_prompt: Optional[str] = None
    ) -> List[ExtractionResult]:
        """
        Extract data from multiple files concurrently with pipeline processing

        Args:
            file_paths (List[str]): List of file paths to extract from
            max_concurrent (int): Maximum number of concurrent extractions (default: 5)
            timeout_seconds (int): Timeout for each file extraction (default: 240)
            extraction_prompt (Optional[str]): Custom prompt for extraction

        Returns:
            List[ExtractionResult]: List of extraction results in the same order as input files
        """
        if not file_paths:
            logger.warning("No files provided for extraction")
            return []

        total_files = len(file_paths)
        results = [None] * total_files  # Pre-allocate to maintain order

        logger.info(f"Starting concurrent extraction of {total_files} files (max {max_concurrent} concurrent)")

        def extract_with_timeout_and_index(file_path: str, index: int) -> tuple[int, ExtractionResult]:
            """Extract single file with timeout and return index for ordering"""
            start_time = time.time()

            try:
                def extraction_task():
                    return self.extract_from_file(file_path, extraction_prompt)

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(extraction_task)
                    try:
                        result = future.result(timeout=timeout_seconds)
                        duration = time.time() - start_time

                        if result.success:
                            logger.info(f"Progress Update:[{index+1}/{total_files}] Completed: {Path(file_path).name} ({duration:.2f}s)")
                        else:
                            logger.error(f"[{index+1}/{total_files}] Failed: {Path(file_path).name} ({duration:.2f}s) - {result.error}")

                        return index, result

                    except TimeoutError:
                        duration = time.time() - start_time
                        logger.warning(f"[{index+1}/{total_files}] Timeout: {Path(file_path).name} ({duration:.2f}s)")
                        return index, ExtractionResult.error_result(
                            f"Extraction timeout after {timeout_seconds} seconds",
                            file_path,
                            Path(file_path).name
                        )
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"[{index+1}/{total_files}] Error: {Path(file_path).name} ({duration:.2f}s) - {e}")
                return index, ExtractionResult.error_result(
                    str(e),
                    file_path,
                    Path(file_path).name
                )

        # Pipeline processing: maintain max_concurrent active extractions
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            active_futures = {}
            remaining_files = list(enumerate(file_paths))  # Keep track of indices
            completed_count = 0

            # Start initial batch of concurrent extractions
            while len(active_futures) < max_concurrent and remaining_files:
                index, file_path = remaining_files.pop(0)
                logger.info(f"[{index+1}/{total_files}] Starting: {Path(file_path).name}")
                future = executor.submit(extract_with_timeout_and_index, file_path, index)
                active_futures[future] = (index, file_path)

            # Process completions and start new extractions
            while active_futures:
                logger.debug(f"Waiting for completion. Active futures: {len(active_futures)}, Completed: {completed_count}/{total_files}")

                # Wait for any extraction to complete
                for completed_future in as_completed(active_futures):
                    index, file_path = active_futures[completed_future]
                    logger.debug(f"Processing completion for: {Path(file_path).name}")

                    try:
                        # Get the result
                        result_index, result = completed_future.result()
                        results[result_index] = result
                        completed_count += 1
                        logger.debug(f"Successfully processed {Path(file_path).name}, completed_count: {completed_count}")

                    except Exception as e:
                        logger.error(f"Unexpected error processing {Path(file_path).name}: {e}")
                        results[index] = ExtractionResult.error_result(str(e), file_path, Path(file_path).name)
                        completed_count += 1
                        logger.debug(f"Error processed {Path(file_path).name}, completed_count: {completed_count}")

                    # Remove completed future
                    del active_futures[completed_future]
                    logger.debug(f"Removed future for {Path(file_path).name}, remaining active: {len(active_futures)}")

                    # Start next file if available
                    if remaining_files:
                        next_index, next_file = remaining_files.pop(0)
                        logger.info(f"[{next_index+1}/{total_files}] Starting: {Path(next_file).name}")
                        new_future = executor.submit(extract_with_timeout_and_index, next_file, next_index)
                        active_futures[new_future] = (next_index, next_file)
                        logger.debug(f"Started new future for {Path(next_file).name}, active futures: {len(active_futures)}")

                    break  # Process one completion at a time

                # Safety check to prevent infinite loop
                if completed_count >= total_files:
                    logger.info(f"All {total_files} files processed, breaking loop")
                    break

        # Count successes and failures
        success_count = sum(1 for result in results if result and result.success)
        failed_count = total_files - success_count

        logger.info(f"Concurrent extraction complete: {success_count} successful, {failed_count} failed")
        return results

def main():
    """Simple demo of the extractor - use test_extraction.py for comprehensive testing"""
    print("Gemini File Extractor Demo")
    print("For comprehensive testing, run: python test_extraction.py")
    print("Supported formats: PDF, JPG, JPEG, PNG, GIF, BMP, WEBP")

if __name__ == "__main__":
    main()