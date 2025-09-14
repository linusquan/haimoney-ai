# HaiMoney AI

AI tools for financial analysis and document extraction using Google Gemini API.

## Overview

This project provides AI-powered tools for extracting financial information from documents including:
- **Basic Facts**: Personal and contact information
- **Assets**: Property, investments, and valuable possessions
- **Liabilities**: Debts, loans, and financial obligations
- **Income**: Salary, business income, and other revenue sources
- **Expenses**: Monthly costs and financial outflows
- **File Extraction**: PDF and image document processing

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Google Gemini API key (set in `.env` file)

## Installation & Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd haimoney-ai
```

### 2. Install Dependencies with uv
This project uses `uv` for fast, reliable dependency management:

```bash
# Install all dependencies (creates .venv automatically)
uv sync

```

### 3. Environment Setup
Create a `.env` file with your API keys:
```bash
cp .env-example .env
# Edit .env and add your Google Gemini API key
```

## Usage

### Running with uv (Recommended)

#### Option 1: Direct Execution
```bash
# Run the main application
uv run python main.py

# Run specific modules
uv run python factfind/main.py

# Run tests
uv run python test/e2e_test.py
```

#### Option 2: Activate Environment
```bash
# Activate the uv environment
uv venv

# Then run normally
python main.py
python factfind/main.py
python test/e2e_test.py
```
