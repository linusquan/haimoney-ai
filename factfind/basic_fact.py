#!/usr/bin/env python3
"""
Basic Fact Extraction Script
Uses OpenAI Responses API to extract structured personal information from combined document content
following the basic_fact.json schema with source tracking.
"""

import logging
import sys
import os
from pathlib import Path
from typing import List, Union
from enum import Enum
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Add parent directory to path to import factfind
sys.path.append(str(Path(__file__).parent))
from factfind import FactFinder
MODEL = 'gpt-5-nano'
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enums for controlled vocabulary
class MaritalStatus(str, Enum):
    """Enumeration for marital status values"""
    MARRIED = "married"
    SINGLE = "single"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    UNKNOWN = "unknown"

# Pydantic models based on basic_fact.json schema
class SimpleField(BaseModel):
    """Standard field structure for simple information extraction"""
    value: Union[str, bool, int, float]
    source: List[str]
    blank: bool

class MaritalStatusField(BaseModel):
    """Field structure for marital status with enum validation"""
    value: Union[MaritalStatus, bool]
    source: List[str]
    blank: bool

class BasicFactExtraction(BaseModel):
    """Schema for extracting basic information with source tracking"""
    firstName: SimpleField
    lastName: SimpleField
    dateOfBirth: SimpleField
    phoneNumber: SimpleField
    email: SimpleField
    currentAddress: SimpleField
    employmentStatus: SimpleField
    annualIncome: SimpleField
    maritalStatus: MaritalStatusField

class BasicFactExtractor:
    def __init__(self, api_key: str = None):
        """
        Initialize the Basic Fact Extractor
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY in .env
        """
        # Load environment variables
        load_dotenv()
        
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Please provide it or set 'OPENAI_API_KEY' in .env file")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully")
    
    def load_system_prompt(self, template_path: str = "basic_info_extract_system_prompt.mustach") -> str:
        """
        Load the system prompt from mustache template file
        
        Args:
            template_path: Path to the mustache template file
            
        Returns:
            System prompt string
        """
        try:
            # Resolve path relative to this script
            if not Path(template_path).is_absolute():
                template_path = Path(__file__).parent / template_path
            
            with open(template_path, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
                
            logger.info(f"System prompt loaded from: {template_path}")
            return prompt
            
        except FileNotFoundError:
            logger.error(f"System prompt template not found: {template_path}")
            raise FileNotFoundError(f"System prompt template not found: {template_path}")
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            raise
    
    def generate_factfind_content(self, extraction_dir: str = "../output/extraction") -> str:
        """
        Generate combined content using factfind.py
        
        Args:
            extraction_dir: Directory containing extracted .md and metadata files
            
        Returns:
            Combined factfind content string
        """
        try:
            # Resolve path relative to this script
            if not Path(extraction_dir).is_absolute():
                extraction_dir = Path(__file__).parent / extraction_dir
            
            logger.info(f"Generating factfind content from: {extraction_dir}")
            
            # Initialize and run fact finder
            fact_finder = FactFinder(str(extraction_dir))
            combined_content = fact_finder.combine_files()
            
            logger.info(f"Generated factfind content: {len(combined_content)} characters")
            return combined_content
            
        except Exception as e:
            logger.error(f"Error generating factfind content: {e}")
            raise
    
    def extract_basic_facts(self, content: str, system_prompt: str) -> BasicFactExtraction:
        """
        Extract basic facts using OpenAI Responses API with structured output
        
        Args:
            content: Combined document content from factfind
            system_prompt: System prompt for extraction
            
        Returns:
            BasicFactExtraction object with structured data
        """
        try:
            logger.info("Extracting basic facts using OpenAI Responses API")
            
            # Create structured output request using the new Responses API
            response = self.client.responses.parse(
                model=MODEL,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                text_format=BasicFactExtraction
            )
            
            logger.info("Successfully extracted basic facts")
            return response.output_parsed
            
        except Exception as e:
            logger.error(f"Error extracting basic facts: {e}")
            raise
    
    def save_results(self, extraction: BasicFactExtraction, output_file: str = "basic_fact_results.json") -> bool:
        """
        Save extraction results to JSON file
        
        Args:
            extraction: BasicFactExtraction object
            output_file: Output file name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            output_path = Path(output_file)
            
            # Convert to dictionary and save as pretty JSON
            result_dict = extraction.model_dump()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving results to {output_file}: {e}")
            return False
    
    def run_extraction(self, extraction_dir: str = "../output/extraction", 
                      template_path: str = "basic_info_extract_system_prompt.mustach",
                      output_file: str = "basic_fact_results.json") -> BasicFactExtraction:
        """
        Run complete basic fact extraction pipeline
        
        Args:
            extraction_dir: Directory containing extracted files
            template_path: Path to system prompt template
            output_file: Output file name
            
        Returns:
            BasicFactExtraction object
        """
        logger.info("Starting basic fact extraction pipeline")
        
        try:
            # Load system prompt
            system_prompt = self.load_system_prompt(template_path)
            
            # Generate factfind content
            content = self.generate_factfind_content(extraction_dir)
            
            # Extract basic facts
            extraction = self.extract_basic_facts(content, system_prompt)
            
            # Save results
            self.save_results(extraction, output_file)
            
            # Print summary
            logger.info("Basic fact extraction complete")
            return extraction
            
        except Exception as e:
            logger.error(f"Extraction pipeline failed: {e}")
            raise

def main():
    """Main function to run the basic fact extractor"""
    try:
        # Initialize extractor
        extractor = BasicFactExtractor()
        
        # Run extraction
        results = extractor.run_extraction()
        
        # Print full JSON results
        import json
        results_json = json.dumps(results.model_dump(), indent=2, ensure_ascii=False)
        print("\nBASIC FACT EXTRACTION RESULTS (JSON):")
        print(results_json)
        
        # Print summary
        print(f"\nResults also saved to: basic_fact_results.json")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())