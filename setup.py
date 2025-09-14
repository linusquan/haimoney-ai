#!/usr/bin/env python3
"""
Setup script for haimoney-ai project
"""

from setuptools import setup, find_packages

setup(
    name="haimoney-ai",
    version="0.1.0",
    description="AI tools for financial analysis and file extraction",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Add your project dependencies here
        # For example: "google-generativeai", "requests", etc.
    ],
    author="Your Name",
    author_email="your.email@example.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)