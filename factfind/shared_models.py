#!/usr/bin/env python3
"""
Shared Pydantic Models
Common models used across different extraction modules.
"""

from pydantic import BaseModel

class DetailedSource(BaseModel):
    """Detailed source information with file path and page number"""
    file_path: str
    page_number: int  # Page number starting from 1