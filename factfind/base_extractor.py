#!/usr/bin/env python3
"""
Base Extractor Class
Common functionality for all document extraction scripts using OpenAI Responses API.
"""

import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic, Type
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Import FactFinder using absolute import
from factfind.fact_aggregator import FactAggregator


logger = logging.getLogger(__name__)

# Generic type for Pydantic models
T = TypeVar('T', bound=BaseModel)

class BaseAnalyser(ABC, Generic[T]):
    """
    Abstract base class for document extraction using OpenAI Responses API
    
    Subclasses must implement:
    - get_model_class(): Return the Pydantic model class
    - get_default_template_path(): Return default template file path
    """
    
    def __init__(self, api_key: str = None, model: str = 'gpt-5-mini'):
        """
        Initialize the extractor
        
        Args:
            api_key: OpenAI API key. If not provided, will look for OPENAI_API_KEY in .env
            model: Model name to use for extraction
        """
        # Load environment variables
        load_dotenv()
        
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Please provide it or set 'OPENAI_API_KEY' in .env file")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info("OpenAI client initialized successfully")
    
    @abstractmethod
    def get_model_class(self) -> Type[T]:
        """Return the Pydantic model class for this extractor"""
        pass
    
    @abstractmethod
    def get_default_template_path(self) -> str:
        """Return the default template file path"""
        pass
    
    
    
    def load_system_prompt(self, template_path: str = None) -> str:
        """
        Load the system prompt from mustache template file
        
        Args:
            template_path: Path to the mustache template file. If None, uses default.
            
        Returns:
            System prompt string
        """
        if template_path is None:
            template_path = self.get_default_template_path()
            
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
            fact_finder = FactAggregator(str(extraction_dir))
            combined_content = fact_finder.combine_files()
            # print('content', combined_content)
            logger.info(f"Generated factfind content: {len(combined_content)} characters")
            return combined_content
            
        except Exception as e:
            logger.error(f"Error generating factfind content: {e}")
            raise
    
    def extract_data(self, content: str, system_prompt: str) -> T:
        """
        Extract data using OpenAI Responses API with structured output
        
        Args:
            content: Combined document content from factfind
            system_prompt: System prompt for extraction
            
        Returns:
            Pydantic model instance with extracted data
        """
        try:
            extraction_type = self.__class__.__name__
            logger.info(f"Extracting data using {extraction_type} with OpenAI Responses API")
            
            # Get the model class for this extractor
            model_class = self.get_model_class()
            
            # Create structured output request using the new Responses API
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "This is the content I would like to be analysed: " + content + "completed analysis content."}
                ],
                text_format=model_class
            )
            
            logger.info(f"Successfully extracted data using {extraction_type}")
            return response.output_parsed
            
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            raise
    
    
    def run_extraction(self, extraction_dir: str = "../output/extraction", 
                      template_path: str = None) -> T:
        """
        Run complete extraction pipeline
        
        Args:
            extraction_dir: Directory containing extracted files
            template_path: Path to system prompt template. If None, uses default.
            
        Returns:
            Pydantic model instance with extracted data
        """
        extraction_type = self.__class__.__name__
        logger.info(f"Starting {extraction_type} pipeline")
        
        try:
            # Load system prompt
            system_prompt = self.load_system_prompt(template_path)
            
            # Generate factfind content
            content = self.generate_factfind_content(extraction_dir)
            
            
            # Extract data
            extraction = self.extract_data(content, system_prompt)
            
            # Print summary
            logger.info(f"{extraction_type} complete")
            return extraction
            
        except Exception as e:
            logger.error(f"{extraction_type} pipeline failed: {e}")
            raise
    
