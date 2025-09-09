#!/usr/bin/env python3
"""
Liability Extraction Script
Uses OpenAI Responses API to extract structured liability information from combined document content
following the liability_info_extract_system_prompt.mst schema for home loan applications.
"""

from pathlib import Path
from typing import List, Type
from enum import Enum
from pydantic import BaseModel, Field

# Import base_extractor using absolute import
from factfind.base_extractor import BaseExtractor

# Enums for controlled vocabulary
class LiabilityType(str, Enum):
    """Enumeration for liability type values"""
    MORTGAGE_LOAN = "Mortgage Loan"
    CREDIT_CARD = "Credit Card"
    PERSONAL_LOAN = "Personal Loan"

# Pydantic models following the exact structure from liability_info_extract_system_prompt.mst
class Liability(BaseModel):
    """Individual liability following the template structure: Type | Description | Interest | Ownership | Lender | Amount | Owning Limit"""
    type: LiabilityType = Field(description="Liability type (e.g., 'Mortgage Loan', 'Credit Card', 'Personal Loan')")
    description: str = Field(description="Liability description/name (e.g., 'cba#8223', 'CBA#0635')")
    interest_rate: str = Field(description="Interest rate in percentage (e.g., '5.73%', '3.8%')")
    ownership: str = Field(description="Ownership details (e.g., 'YZ 100.0%', 'YZ 50.0% - YO 50.0%')")
    lender: str = Field(description="Lender's name (e.g., 'CBA', 'Bankwest')")
    amount_owing: float = Field(ge=0, description="Amount owing as number (e.g., 639392, 40000)")
    limit: float = Field(ge=0, description="Limit of liability, for credit cards this is the limit, for others equal to amount owing")
    source: List[str] = Field(default=[], description="Source documents where this liability was found")

class MultipleApplicantsLiabilities(BaseModel):
    """Schema for extracting liability information from multiple applicants"""
    liabilities: List[Liability] = Field(description="List of all liabilities found in the documents")

class LiabilityExtractor(BaseExtractor[MultipleApplicantsLiabilities]):
    """Liability extractor using BaseExtractor"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key, model='gpt-5-mini')
    
    def get_model_class(self) -> Type[MultipleApplicantsLiabilities]:
        """Return the Pydantic model class for liability extraction"""
        return MultipleApplicantsLiabilities
    
    def get_default_template_path(self) -> str:
        """Return the default template file path"""
        return str(Path(__file__).parent / "liability_info_extract_system_prompt.mst")