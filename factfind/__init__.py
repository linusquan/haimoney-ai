"""
Factfind package for document extraction and analysis.

This package provides functionality for extracting structured information from documents
using OpenAI's structured output capabilities.
"""

# Import modules
from factfind.asset import AssetAnalyser, Asset, AssetsExtraction, AssetCategory
from factfind.income import IncomeAnalyser, Income, IncomeExtraction, IncomeType, IncomeFrequency
from factfind.basic import BasicFactAnalyser, BasicFactExtraction, MultipleApplicantsExtraction, MaritalStatus

__all__ = [
    'AssetAnalyser', 'Asset', 'AssetsExtraction', 'AssetCategory',
    'IncomeAnalyser', 'Income', 'IncomeExtraction', 'IncomeType', 'IncomeFrequency',
    'BasicFactAnalyser', 'BasicFactExtraction', 'MultipleApplicantsExtraction', 'MaritalStatus'
]