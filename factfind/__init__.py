"""
Factfind package for document extraction and analysis.

This package provides functionality for extracting structured information from documents
using OpenAI's structured output capabilities.
"""

# Import modules
from factfind.asset import AssetExtractor, Asset, AssetsExtraction, AssetCategory
from factfind.income import IncomeExtractor, Income, IncomeExtraction, IncomeType, IncomeFrequency
from factfind.basic import BasicFactExtractor, BasicFactExtraction, MultipleApplicantsExtraction, MaritalStatus

__all__ = [
    'AssetExtractor', 'Asset', 'AssetsExtraction', 'AssetCategory',
    'IncomeExtractor', 'Income', 'IncomeExtraction', 'IncomeType', 'IncomeFrequency',
    'BasicFactExtractor', 'BasicFactExtraction', 'MultipleApplicantsExtraction', 'MaritalStatus'
]