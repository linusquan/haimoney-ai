#!/usr/bin/env python3
"""
Basic Fact Extraction Script
Uses OpenAI Responses API to extract structured personal information from combined document content
following the basic_fact.json schema with source tracking.
"""

import sys
from pathlib import Path
from typing import List, Union, Type
from enum import Enum
from pydantic import BaseModel

# Add parent directory to path to import base_extractor
sys.path.append(str(Path(__file__).parent))
from base_extractor import BaseExtractor

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
    """Schema for extracting basic information with source tracking for a single applicant"""
    firstName: SimpleField
    lastName: SimpleField
    dateOfBirth: SimpleField
    phoneNumber: SimpleField
    email: SimpleField
    currentAddress: SimpleField
    employmentStatus: SimpleField
    annualIncome: SimpleField
    maritalStatus: MaritalStatusField

class MultipleApplicantsExtraction(BaseModel):
    """Schema for extracting information from multiple applicants"""
    applicants: List[BasicFactExtraction]

class BasicFactExtractor(BaseExtractor[MultipleApplicantsExtraction]):
    """Basic fact extractor using BaseExtractor"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key, model='gpt-5-nano')
    
    def get_model_class(self) -> Type[MultipleApplicantsExtraction]:
        """Return the Pydantic model class for basic fact extraction"""
        return MultipleApplicantsExtraction
    
    def get_default_template_path(self) -> str:
        """Return the default template file path"""
        return "basic_info_extract_system_prompt.mst"
    
