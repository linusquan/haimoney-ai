"""
Basic fact extraction module for factfind package.

This module provides functionality for extracting basic personal information from documents
using OpenAI's structured output capabilities.
"""

from factfind.basic.basic_fact import BasicFactExtractor, BasicFactExtraction, MultipleApplicantsExtraction, MaritalStatus

__all__ = ['BasicFactExtractor', 'BasicFactExtraction', 'MultipleApplicantsExtraction', 'MaritalStatus']