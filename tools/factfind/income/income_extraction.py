#!/usr/bin/env python3
"""
Income Extraction Script
Uses OpenAI Responses API to extract structured income information from combined document content
following the income_extraction_system_prompt.mst schema for home loan applications.
"""

from pathlib import Path
from typing import List, Type, Optional
from enum import Enum
from pydantic import BaseModel, Field

# Import base_extractor and shared models using absolute import
from tools.factfind.base_extractor import BaseAnalyser
from tools.factfind.shared_models import DetailedSource

# Enums for controlled vocabulary
class IncomeType(str, Enum):
    """Enumeration for income type values"""
    BASE_SALARY = "Base Salary"
    REGULAR_OVERTIME = "Regular Overtime"
    BONUS = "Bonus"
    COMMISSION = "Commission"
    WORK_ALLOWANCE = "Work Allowance"
    WORKERS_COMPENSATION = "Workers Compensation"
    GOVERNMENT_BENEFITS = "Government Benefits"
    PRIVATE_PENSION = "Private Pension"
    ADDBACK = "Addback"
    ANNUITIES = "Annuities"
    COMPANY_PROFIT_BEFORE_TAX = "Company Profit Before Tax"
    DIVIDENDS = "Dividends"
    FOREIGN_SOURCED = "Foreign Sourced"
    INTEREST_INCOME = "Interest Income"
    RENTAL_INCOME = "Rental Income"
    OTHER_INCOME = "Other Income"

class IncomeFrequency(str, Enum):
    """Enumeration for income frequency values"""
    ANNUALLY = "Annually"
    MONTHLY = "Monthly"
    FORTNIGHTLY = "Fortnightly"
    WEEKLY = "Weekly"

# Pydantic models following the exact structure from income_extraction_system_prompt.mst
class Income(BaseModel):
    """Individual income following the template structure: Type | Company | Ownership | Frequency | Amount"""
    type: IncomeType = Field(description="Income type (e.g., 'Base Salary', 'Company Profit Before Tax', 'Rental Income')")
    company: Optional[str] = Field(default="", description="Company name (e.g., 'WOK N ROLL (AUST) PTY LTD'), only applicable for salary")
    ownership: str = Field(description="Ownership details (e.g., 'Yong Hong Zhou', 'YZ 50.0% - YO 50.0%')")
    frequency: IncomeFrequency = Field(description="Income frequency (e.g., 'Annually', 'Monthly', 'Fortnightly', 'Weekly')")
    amount: float = Field(ge=0, description="Income amount as number (e.g., 1465535, 20160, 2400)")
    source: List[DetailedSource] = Field(default=[], description="Source documents where this income was found")

class IncomeExtraction(BaseModel):
    """Schema for extracting income information from multiple applicants"""
    incomes: List[Income] = Field(description="List of all incomes found in the documents")

class IncomeAnalyser(BaseAnalyser[IncomeExtraction]):
    """Income extractor using BaseExtractor"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key, model='gpt-5-mini')
    
    def get_model_class(self) -> Type[IncomeExtraction]:
        """Return the Pydantic model class for income extraction"""
        return IncomeExtraction
    
    def get_default_template_path(self) -> str:
        """Return the default template file path"""
        return str(Path(__file__).parent / "income_extraction_system_prompt.mst")