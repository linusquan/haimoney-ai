#!/usr/bin/env python3
"""
LLM File Analysis Service
Core service for analyzing files through concurrent extraction and category-based analysis.

Input: List of file paths
- Calls gemini_file_extract.py for concurrent file extraction
- Stores results and metadata with UUID-based naming
- Invokes relevant analyzers based on category (basic, asset, expense, liability)
"""

import json
import uuid
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import extraction tools
from tools.file_extract.gemini_file_extract import GeminiFileExtractor, ExtractionResult

# Import category analyzers
from tools.factfind.basic.basic_fact import BasicFactAnalyser
from tools.factfind.asset.asset_extraction import AssetAnalyser
from tools.factfind.expense.expense_extraction import ExpenseAnalyser
from tools.factfind.income.income_extraction import IncomeAnalyser
from tools.factfind.liability.liability_extraction import LiabilityAnalyser

logger = logging.getLogger(__name__)

@dataclass
class LLMAnalysisResult:
    """Result from file analysis operation"""
    success: bool
    analysis_id: str
    files_processed: int
    extraction_results: List[Dict[str, Any]]
    category_analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0

    @classmethod
    def success_result(cls, analysis_id: str, files_processed: int,
                      extraction_results: List[Dict[str, Any]],
                      category_analysis: Optional[Dict[str, Any]] = None,
                      duration_seconds: float = 0.0) -> 'LLMAnalysisResult':
        """Create successful analysis result"""
        return cls(
            success=True,
            analysis_id=analysis_id,
            files_processed=files_processed,
            extraction_results=extraction_results,
            category_analysis=category_analysis,
            duration_seconds=duration_seconds
        )

    @classmethod
    def error_result(cls, error: str, analysis_id: str = None) -> 'LLMAnalysisResult':
        """Create error analysis result"""
        return cls(
            success=False,
            analysis_id=analysis_id or str(uuid.uuid4()),
            files_processed=0,
            extraction_results=[],
            error=error
        )

class LLMFileAnalysisService:
    """
    Main service class for LLM-based file analysis

    Handles concurrent file extraction, result storage, and category-based analysis
    """

    def __init__(self, output_dir: str = "output",
                 timeout_seconds: int = 240):
        """
        Initialize the analysis service

        Args:
            output_dir: Base output directory for results
            max_concurrent: Maximum concurrent file extractions
            timeout_seconds: Timeout for individual file extractions
        """
        self.output_dir = Path(output_dir).resolve()
        self.timeout_seconds = timeout_seconds

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "extraction").mkdir(exist_ok=True)

        # Initialize file extractor
        try:
            self.extractor = GeminiFileExtractor()
            logger.info("Gemini File Extractor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini extractor: {e}")
            raise

        # Category analyzer mapping
        self.analyzers = {
            "basic": BasicFactAnalyser,
            "asset": AssetAnalyser,
            "expense": ExpenseAnalyser,
            "income": IncomeAnalyser,
            "liability": LiabilityAnalyser
        }

    def _generate_analysis_id(self) -> str:
        """Generate unique analysis ID"""
        return str(uuid.uuid4())

    def _get_extraction_paths(self, analysis_id: str) -> tuple[Path, Path]:
        """
        Get paths for extraction results

        Args:
            analysis_id: Unique analysis identifier

        Returns:
            Tuple of (extraction_dir, metadata_file)
        """
        extraction_dir = self.output_dir / f"extraction-{analysis_id}"
        metadata_file = self.output_dir / f"extraction-{analysis_id}-metadata.json"

        extraction_dir.mkdir(parents=True, exist_ok=True)
        return extraction_dir, metadata_file

    def _get_category_paths(self, analysis_id: str, category: str) -> tuple[Path, Path]: # this is questionable
        """
        Get paths for category analysis results

        Args:
            analysis_id: Unique analysis identifier
            category: Analysis category (basic, asset, etc.)

        Returns:
            Tuple of (result_file, metadata_file)
        """
        result_file = self.output_dir / f"{category}-{analysis_id}.json"
        return result_file

    def _save_extraction_results(self, results: List[ExtractionResult],
                                analysis_id: str, duration: float) -> bool:
        """
        Save extraction results using pattern from extractor.py

        Args:
            results: List of extraction results
            analysis_id: Unique analysis identifier
            duration: Total extraction duration

        Returns:
            True if successful, False otherwise
        """
        try:
            extraction_dir, metadata_file = self._get_extraction_paths(analysis_id)

            # Save individual file results as .md and metadata files
            extraction_summaries = []
            for result in results:
                if result.filename:
                    base_name = Path(result.filename).stem
                    md_path = extraction_dir / f"{base_name}.md"
                    file_metadata_path = extraction_dir / f"{base_name}-hmoney-metadata.json"

                    # Save markdown content
                    if result.success and result.result:
                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(result.result)
                    else:
                        # Create empty markdown file for failed extractions
                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(f"# Extraction Failed\n\n**Error:** {result.error or 'Unknown error'}\n")

                    # Save individual file metadata
                    file_metadata = {
                        "filename": result.filename,
                        "description": result.description or "",
                        "error": not result.success,
                        "errorReason": result.error or "",
                        "file_path": result.file_path
                    }

                    with open(file_metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(file_metadata, f, indent=2, ensure_ascii=False)

                    extraction_summaries.append({
                        "filename": result.filename,
                        "success": result.success,
                        "md_path": str(md_path),
                        "metadata_path": str(file_metadata_path),
                        "error": result.error
                    })

            # Save overall extraction metadata
            overall_metadata = {
                "analysis_id": analysis_id,
                "extraction_dir": str(extraction_dir),
                "total_files": len(results),
                "successful_extractions": sum(1 for r in results if r.success),
                "failed_extractions": sum(1 for r in results if not r.success),
                "duration_seconds": round(duration, 2),
                "files": extraction_summaries,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(overall_metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Extraction results saved to {extraction_dir}")
            logger.info(f"Extraction metadata saved to {metadata_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save extraction results: {e}")
            return False

    def extract_files(self, file_paths: List[str]) -> tuple[List[ExtractionResult], str, float]:
        """
        Extract content from multiple files concurrently

        Args:
            file_paths: List of file paths to extract from
            extraction_prompt: Optional custom extraction prompt

        Returns:
            Tuple of (extraction_results, analysis_id, duration_seconds)
        """
        if not file_paths:
            raise ValueError("No file paths provided")

        analysis_id = self._generate_analysis_id()
        logger.info(f"Starting file extraction for analysis {analysis_id}")
        logger.info(f"Processing {len(file_paths)} files with max 5 concurrent")

        start_time = time.time()

        # Use the extractor's concurrent processing
        results = self.extractor.extract_multiple_files(
            file_paths=file_paths,
            max_concurrent=5,
            timeout_seconds=self.timeout_seconds
        )

        duration = time.time() - start_time

        # Save results using extractor.py pattern
        save_success = self._save_extraction_results(results, analysis_id, duration)
        if not save_success:
            logger.warning("Failed to save some extraction results")

        logger.info(f"File extraction complete for analysis {analysis_id}: {duration:.2f}s")
        return results, analysis_id, duration

    def analyze_by_category(self, analysis_id: str, category: str) -> Optional[Dict[str, Any]]:
        """
        Perform category-based analysis on extracted files

        Args:
            analysis_id: Analysis ID from file extraction
            category: Analysis category (basic, asset, expense, income, liability)

        Returns:
            Analysis results dict or None if failed
        """
        if category not in self.analyzers:
            logger.error(f"Unknown category: {category}. Available: {list(self.analyzers.keys())}")
            return None

        logger.info(f"Starting {category} analysis for {analysis_id}")

        try:
            # Get extraction directory path
            extraction_dir = self.output_dir / f"extraction-{analysis_id}"

            if not extraction_dir.exists():
                logger.error(f"Extraction directory not found: {extraction_dir}")
                return None

            # Initialize the appropriate analyzer
            analyzer_class = self.analyzers[category]
            analyzer = analyzer_class()

            # Run the analysis using the extraction directory
            start_time = time.time()
            logger.info(f"Running {category} analyzer on extraction directory: {extraction_dir}")

            try:
                # Convert to absolute path for analyzer
                abs_extraction_dir = extraction_dir.resolve()
                logger.info(f"Using absolute path for analyzer: {abs_extraction_dir}")
                analysis_result = analyzer.run_extraction(str(abs_extraction_dir))
                logger.info(f"Analysis result obtained: {type(analysis_result)}")
            except Exception as analyzer_error:
                logger.error(f"Analyzer execution failed: {analyzer_error}")
                raise analyzer_error

            duration = time.time() - start_time
            logger.info(f"Analysis completed in {duration:.2f}s")

            # Save category analysis results
            result_file = self._get_category_paths(analysis_id, category)

            # Convert Pydantic model to dict for JSON serialization
            if hasattr(analysis_result, 'model_dump'):
                analysis_data = analysis_result.model_dump()
            elif hasattr(analysis_result, 'dict'):
                analysis_data = analysis_result.dict()
            else:
                analysis_data = analysis_result.__dict__

            # Save analysis result
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)

            logger.info(f"{category} analysis complete: {duration:.2f}s")
            logger.info(f"Results saved to {result_file}")

            return {
                "category": category,
                "result": analysis_data
            }

        except Exception as e:
            logger.error(f"Category analysis failed for {category}: {e}")
            return None

    def analyze_files(self, folder_path: str,
                     category: str) -> LLMAnalysisResult:
        """
        Complete analysis pipeline: extract files and perform category analysis

        Args:
            folder_path: Path to folder containing files to analyze
            category: Category to analyze (basic, asset, expense, income, liability)

        Returns:
            AnalysisResult with complete analysis results
        """
        if not folder_path:
            return LLMAnalysisResult.error_result("No folder path provided")

        # Discover files in the folder
        folder = Path(folder_path)
        if not folder.exists():
            return LLMAnalysisResult.error_result(f"Folder does not exist: {folder_path}")

        if not folder.is_dir():
            return LLMAnalysisResult.error_result(f"Path is not a directory: {folder_path}")

        # Find supported files
        supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_paths = []
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                file_paths.append(str(file_path))

        if not file_paths:
            return LLMAnalysisResult.error_result(f"No supported files found in folder: {folder_path}")

        logger.info(f"Found {len(file_paths)} supported files in {folder_path}")

        overall_start_time = time.time()

        try:
            # Step 1: Extract files concurrently
            extraction_results, analysis_id, _ = self.extract_files(
                file_paths
            )

            # Prepare extraction summaries
            extraction_summaries = []
            for result in extraction_results:
                extraction_summaries.append({
                    "filename": result.filename,
                    "success": result.success,
                    "file_path": result.file_path,
                    "error": result.error,
                    "description": result.description
                })

            # Step 2: Category analysis
            category_result = None
            if category:
                logger.info(f"Running category analysis for: {category}")
                category_result = self.analyze_by_category(analysis_id, category)
                if not category_result:
                    logger.warning(f"Category analysis failed for: {category}")

            total_duration = time.time() - overall_start_time
            successful_extractions = sum(1 for r in extraction_results if r.success)

            logger.info(f"Complete analysis finished for {analysis_id}: {total_duration:.2f}s")
            logger.info(f"Files: {len(file_paths)}, Successful extractions: {successful_extractions}")

            return LLMAnalysisResult.success_result(
                analysis_id=analysis_id,
                files_processed=len(file_paths),
                extraction_results=extraction_summaries,
                category_analysis=category_result,
                duration_seconds=total_duration
            )

        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}")
            return LLMAnalysisResult.error_result(str(e))

def main():
    """Simple demo of the LLM File Analysis Service"""
    print("LLM File Analysis Service")
    print("Core service for analyzing files through concurrent extraction and category-based analysis.")
    print()
    print("Available categories: basic, asset, expense, income, liability")
    print()
    print("Usage example:")
    print("  service = LLMFileAnalysisService(output_dir='output')")
    print("  result = service.analyze_files('path/to/folder', 'basic')")
    print()
    print("For comprehensive testing, run:")
    print("  python test/extract_and_basic_analysis.py")

if __name__ == "__main__":
    main()