#!/usr/bin/env python3
"""
Expense Extraction Script
Uses OpenAI Responses API to extract structured expense information from combined document content
following the expense_system_prompt.mst schema for home loan applications.
"""

from pathlib import Path
from typing import List, Type
from enum import Enum
from pydantic import BaseModel, Field

# Import base_extractor and shared models using absolute import
from tools.factfind.base_extractor import BaseAnalyser
from tools.factfind.shared_models import DetailedSource

# Enums for controlled vocabulary
class ExpenseType(str, Enum):
    """Enumeration for expense type values"""
    BOARD = "Board"
    CHILD_CARE = "Child Care"
    CHILD_MAINTENANCE = "Child Maintenance"
    CLOTHING_PERSONAL_CARE = "Clothing & Personal Care"
    ELECTRICITY = "Electricity"
    ENTERTAINMENT = "Entertainment"
    GAS = "Gas"
    GROCERIES = "Groceries"
    HEALTH_CARE = "Health Care"
    HIGHER_EDUCATION_VOCATIONAL = "Higher Education and Vocational Training"
    HOLIDAY_HOME_COSTS = "Holiday Home Costs"
    HOME_CONTENTS_INSURANCE = "Home & Contents Insurance"
    HOME_MAINTENANCE = "Home Maintenance"
    INVESTMENT_PROPERTY_COSTS = "Investment Property Costs"
    MEDICAL_LIFE_INSURANCE = "Medical and Life Insurance"
    OTHER = "Other"
    OTHER_INSURANCES = "Other Insurances"
    OWNER_OCCUPIED_COUNCIL_WATER = "Owner Occupied Council & Water Rates"
    PET_CARE = "Pet Care"
    PRIVATE_NON_GOVERNMENT_EDUCATION = "Private and Non-Government Education"
    PUBLIC_PRIMARY_SECONDARY_EDUCATION = "Public Primary and Secondary Education"
    RENTAL_EXPENSES = "Rental Expenses"
    STRATA_FEES_LAND_TAX = "Strata Fees and Land Tax"
    TELEPHONE_INTERNET = "Telephone and Internet"
    VEHICLE_INSURANCE = "Vehicle Insurance"
    VEHICLE_MAINTENANCE_TRANSPORT = "Vehicle Maintenance & Transport"
    WATER = "Water"

class ExpenseFrequency(str, Enum):
    """Enumeration for expense frequency values"""
    ANNUALLY = "Annually"
    MONTHLY = "Monthly"
    FORTNIGHTLY = "Fortnightly"
    WEEKLY = "Weekly"

# Pydantic models following the exact structure from expense_system_prompt.mst
class Expense(BaseModel):
    """Individual expense following the template structure: Type | Ownership | Frequency | Amount"""
    type: ExpenseType = Field(description="Expense type (e.g., 'Electricity', 'Groceries', 'Entertainment')")
    ownership: str = Field(description="Ownership details (e.g., 'YZ 50.0% - YO 50.0%', 'MZ 100.0%')")
    frequency: ExpenseFrequency = Field(description="Frequency of expense (e.g., 'Monthly', 'Annually')")
    amount: float = Field(ge=0, description="Amount as number (e.g., 800, 200, 2000)")
    source: List[DetailedSource] = Field(default=[], description="Source documents where this expense was found in detail to file path and page, if there are multiple pages, use the most relevant page")
    reason: str = Field(description="Reasons to how this expense is counted in 200 words sumary: e.g. the applicant has 500$ shown on the city countil bill quaterly.")

class ExpenseExtraction(BaseModel):
    """Schema for extracting expense information from multiple applicants"""
    expenses: List[Expense] = Field(description="List of all expenses found in the documents")

class ExpenseAnalyser(BaseAnalyser[ExpenseExtraction]):
    """Expense extractor using BaseExtractor"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key, model='gpt-5-mini')
    
    def get_model_class(self) -> Type[ExpenseExtraction]:
        """Return the Pydantic model class for expense extraction"""
        return ExpenseExtraction
    
    def get_default_template_path(self) -> str:
        """Return the default template file path"""
        return str(Path(__file__).parent / "expense_system_prompt.mst")