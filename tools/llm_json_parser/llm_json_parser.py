#!/usr/bin/env python3
"""
LLM JSON Parser
Uses OpenAI GPT models to fix invalid JSON strings while preserving all information.

This tool addresses common JSON parsing issues such as:
- Invalid escape sequences (e.g., \r characters)
- Malformed JSON structure
- Missing quotes or brackets
- Incorrect formatting

The LLM intelligently fixes the JSON while maintaining all original data.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class JSONParseResult:
    """Result of JSON parsing operation"""
    success: bool
    parsed_json: Optional[Dict[Any, Any]] = None
    original_text: Optional[str] = None
    fixed_text: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def success_result(cls, parsed_json: Dict[Any, Any], original_text: str, fixed_text: str) -> 'JSONParseResult':
        """Create successful parse result"""
        return cls(success=True, parsed_json=parsed_json, original_text=original_text, fixed_text=fixed_text)

    @classmethod
    def error_result(cls, error: str, original_text: str = None) -> 'JSONParseResult':
        """Create error parse result"""
        return cls(success=False, error=error, original_text=original_text)


class LLMJSONParser:
    """
    Uses OpenAI GPT models to fix and parse invalid JSON strings
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM JSON Parser

        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY in .env
            model: OpenAI model to use (default: gpt-3.5-turbo)
        """
        if not api_key:
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Please provide it or set 'OPENAI_API_KEY' in .env file")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized LLM JSON Parser with model: {model}")

    def _create_fix_prompt(self, invalid_json: str) -> str:
        """Create prompt for fixing invalid JSON"""
        return f"""You are a JSON repair specialist. Fix the following invalid JSON string to make it valid Python JSON while preserving ALL original information.

Common issues to fix:
1. Invalid escape sequences (\\r should become \\n or be properly escaped)
2. Unescaped quotes within strings
3. Missing brackets or braces
4. Incorrect formatting

CRITICAL REQUIREMENTS:
- Preserve ALL original data and content
- Do not summarize, truncate, or modify the actual content
- Only fix structural/formatting issues
- Return ONLY the fixed JSON, no explanation or markdown formatting
- Ensure the result can be parsed by Python's json.loads()

Invalid JSON to fix:
{invalid_json}

Fixed JSON:"""

    def fix_json_string(self, invalid_json: str) -> JSONParseResult:
        """
        Fix an invalid JSON string using OpenAI GPT

        Args:
            invalid_json: The invalid JSON string to fix

        Returns:
            JSONParseResult: Result containing fixed JSON or error information
        """
        try:
            # First try to parse as-is
            try:
                parsed = json.loads(invalid_json)
                logger.info("JSON is already valid, no fixing needed")
                return JSONParseResult.success_result(parsed, invalid_json, invalid_json)
            except json.JSONDecodeError:
                logger.info("JSON is invalid, attempting LLM fix...")

            # Try basic cleanup first (faster than LLM call)
            cleaned_json = self._basic_cleanup(invalid_json)
            try:
                parsed = json.loads(cleaned_json)
                logger.info("JSON fixed with basic cleanup")
                return JSONParseResult.success_result(parsed, invalid_json, cleaned_json)
            except json.JSONDecodeError:
                logger.info("Basic cleanup failed, using LLM...")

            # Use LLM to fix the JSON
            prompt = self._create_fix_prompt(invalid_json)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent formatting
            )

            fixed_json_text = response.choices[0].message.content.strip()

            # Remove any markdown code blocks if present
            if fixed_json_text.startswith('```'):
                lines = fixed_json_text.split('\n')
                # Remove first line if it's ```json or ```
                if lines[0].startswith('```'):
                    lines = lines[1:]
                # Remove last line if it's ```
                if lines[-1].strip() == '```':
                    lines = lines[:-1]
                fixed_json_text = '\n'.join(lines)

            # Validate the fixed JSON
            try:
                parsed_json = json.loads(fixed_json_text)
                logger.info("Successfully fixed JSON using LLM")
                return JSONParseResult.success_result(parsed_json, invalid_json, fixed_json_text)

            except json.JSONDecodeError as e:
                error_msg = f"LLM failed to produce valid JSON: {str(e)}"
                logger.error(error_msg)
                logger.error(f"LLM output: {fixed_json_text[:500]}...")
                return JSONParseResult.error_result(error_msg, invalid_json)

        except Exception as e:
            error_msg = f"Error during JSON fixing: {str(e)}"
            logger.error(error_msg)
            return JSONParseResult.error_result(error_msg, invalid_json)

    def _basic_cleanup(self, json_text: str) -> str:
        """
        Perform basic cleanup operations before using LLM

        Args:
            json_text: The JSON text to clean

        Returns:
            Cleaned JSON text
        """
        # Replace common problematic characters
        cleaned = json_text.replace('\r\n', '\n').replace('\r', '\n')

        # Fix common escape sequence issues
        # Note: This is basic cleanup, LLM will handle complex cases

        return cleaned

    def parse_file(self, file_path: str) -> JSONParseResult:
        """
        Parse JSON from a file

        Args:
            file_path: Path to the JSON file

        Returns:
            JSONParseResult: Result containing parsed JSON or error information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return JSONParseResult.error_result(f"File not found: {file_path}")

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.fix_json_string(content)

        except Exception as e:
            return JSONParseResult.error_result(f"Error reading file: {str(e)}")

    def save_fixed_json(self, result: JSONParseResult, output_path: str) -> bool:
        """
        Save fixed JSON to a file

        Args:
            result: JSONParseResult from fix_json_string()
            output_path: Path to save the fixed JSON

        Returns:
            True if successful, False otherwise
        """
        try:
            if not result.success:
                logger.error(f"Cannot save failed parse result: {result.error}")
                return False

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result.parsed_json, f, indent=2, ensure_ascii=False)

            logger.info(f"Fixed JSON saved to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving fixed JSON: {str(e)}")
            return False
