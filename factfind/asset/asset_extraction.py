#!/usr/bin/env python3
"""
Asset Extraction Script
Uses OpenAI Responses API to extract structured asset information from combined document content
following the financial_detail_extraction.mst schema for home loan applications.
"""

from pathlib import Path
from typing import List, Type
from enum import Enum
from pydantic import BaseModel, Field

# Import base_extractor using absolute import
from factfind.base_extractor import BaseExtractor

# Enums for controlled vocabulary
class AssetCategory(str, Enum):
    """Enumeration for asset category values"""
    REAL_ESTATE = "Real Estate"
    DEPOSIT_ACCOUNT = "Deposit Account"
    MANAGED_FUND = "Managed Fund"
    PERSONAL_EQUITY_IN_ANY_PRIVATE_BUSINESS = "Personal Equity In Any Private Business"
    SHARES = "Shares"
    SUPERANNUATION = "Superannuation"
    BOAT = "Boat"
    MOTORCYCLE = "Motorcycle"
    MOTOR_VEHICLE = "Motor Vehicle"
    TRUCK = "Truck"
    MARINE = "Marine"
    CARAVAN_HORSE_FLOAT = "Caravan/Horse Float"
    PLANT_AND_EQUIPMENT = "Plant and Equipment"
    STOCK_MACHINERY = "Stock Machinery"
    TOOLS_OF_TRADE = "Tools of Trade"
    CHARGE_OVER_CASH = "Charge Over Cash"
    COLLECTIONS = "Collections"
    DEBENTURE_CHARGE = "Debenture Charge"
    GOODWILL = "Goodwill"
    GUARANTEE = "Guarantee"
    RECEIVABLES = "Receivables"
    HOME_CONTENTS = "Home Contents"
    LIFE_INSURANCE = "Life Insurance"
    OTHER = "Other"

# Pydantic models following the exact structure from financial_detail_extraction.mst
class Asset(BaseModel):
    """Individual asset following the template structure: Category | Description | Ownership | Value | Valuation Type"""
    category: AssetCategory = Field(description="Asset category (e.g., 'Real Estate', 'Motor Vehicle')")
    description: str = Field(description="Asset description/name (e.g., 'INV-5 Strutt Cr Metford', 'Benz S600')")
    ownership: str = Field(description="Ownership details (e.g., 'YZ 100.0%', 'YZ 50.0% - YO 50.0%')")
    value: float = Field(ge=0, description="Asset value as number (e.g., 992000, 300000)")
    valuationBasis: str = Field(description="basis of valuation (e.g., 'Applicant Estimate', 'Certified Valuation')")
    source: List[str] = Field(default=[], description="Source documents where this asset was found")

class AssetsExtraction(BaseModel):
    """Schema for extracting asset information from multiple applicants"""
    assets: List[Asset] = Field(description="List of all assets found in the documents")

class AssetExtractor(BaseExtractor[AssetsExtraction]):
    """Asset extractor using BaseExtractor"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key, model='gpt-5-mini')
    
    def get_model_class(self) -> Type[AssetsExtraction]:
        """Return the Pydantic model class for asset extraction"""
        return AssetsExtraction
    
    def get_default_template_path(self) -> str:
        """Return the default template file path"""
        return str(Path(__file__).parent / "asset_detail_extraction.mst")
    
