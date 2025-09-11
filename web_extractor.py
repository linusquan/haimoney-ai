#!/usr/bin/env python3
"""
Web Interface for File Extractor
Provides a web-based interface to start extraction process and monitor progress.
"""

import os
import sys
import json
import logging
import threading
import time
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the current directory to Python path to import extractor and factfind
sys.path.append(os.path.dirname(__file__))
from extractor import FileProcessor

# Import factfind modules for direct analysis
from factfind.basic.basic_fact import BasicFactAnalyser
from factfind.asset.asset_extraction import AssetAnalyser
from factfind.liability.liability_extraction import LiabilityAnalyser
from factfind.income.income_extraction import IncomeAnalyser
from factfind.expense.expense_extraction import ExpenseAnalyser
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging for web application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'extraction_web_interface'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state for tracking extraction progress
extraction_state = {
    "is_running": False,
    "total_files": 0,
    "completed_files": 0,
    "current_file": "",
    "results": None,
    "error": None
}

# Global state for tracking analysis progress
analysis_state = {
    "is_running": False,
    "current_stage": "",
    "results": {
        "basic_fact": None,
        "asset": None,
        "liability": None,
        "income": None,
        "expense": None
    }
}

class AnalysisFileHandler(FileSystemEventHandler):
    """Handles file system events for analysis results"""
    
    def __init__(self):
        super().__init__()
        self.target_files = {"basic_fact.json", "asset.json", "liability.json", "income.json", "expense.json"}
    
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.name in self.target_files:
            self.process_analysis_file(file_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.name in self.target_files:
            self.process_analysis_file(file_path)
    
    def process_analysis_file(self, file_path):
        """Process analysis result file and emit to clients"""
        try:
            time.sleep(0.1)  # Brief delay to ensure file is fully written
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            category = file_path.stem  # e.g., "basic_fact" from "basic_fact.json"
            analysis_state["results"][category] = data
            
            logger.info(f"Analysis result loaded: {category}")
            
            # Emit to clients
            socketio.emit('analysis_result', {
                'category': category,
                'data': data,
                'message': f'{category.replace("_", " ").title()} analysis complete'
            })
            
        except Exception as e:
            logger.error(f"Error processing analysis file {file_path}: {e}")

# Initialize file watcher
analysis_handler = AnalysisFileHandler()
observer = Observer()
result_dir = Path("output/result")
result_dir.mkdir(parents=True, exist_ok=True)
observer.schedule(analysis_handler, str(result_dir), recursive=False)

def load_existing_analysis_results():
    """Load existing analysis results from output/result directory"""
    global analysis_state
    
    target_files = {
        "basic_fact.json": "basic_fact",
        "asset.json": "asset", 
        "liability.json": "liability",
        "income.json": "income",
        "expense.json": "expense"
    }
    
    for filename, category in target_files.items():
        file_path = result_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                analysis_state["results"][category] = data
                logger.info(f"Loaded existing analysis result: {category}")
            except Exception as e:
                logger.error(f"Error loading existing analysis file {filename}: {e}")
    
    return analysis_state["results"]

class WebFileProcessor(FileProcessor):
    """Extended FileProcessor that emits progress updates via WebSocket"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.web_total_files = 0
        self.web_completed_files = 0
    
    def process_file(self, file_path, index, total):
        """Override to emit progress updates"""
        global extraction_state
        
        # Update current file being processed
        extraction_state["current_file"] = file_path.name
        socketio.emit('progress_update', {
            'current_file': file_path.name,
            'total_files': self.web_total_files,
            'completed_files': self.web_completed_files,
            'status': f'Processing {file_path.name}...'
        })
        
        # Call parent method
        result = super().process_file(file_path, index, total)
        
        # Update completion count if successful
        if result["success"]:
            self.web_completed_files += 1
            extraction_state["completed_files"] = self.web_completed_files
            
            socketio.emit('progress_update', {
                'current_file': file_path.name,
                'total_files': self.web_total_files,
                'completed_files': self.web_completed_files,
                'status': f'Completed {file_path.name} ✅'
            })
        else:
            socketio.emit('progress_update', {
                'current_file': file_path.name,
                'total_files': self.web_total_files,
                'completed_files': self.web_completed_files,
                'status': f'Failed {file_path.name} ❌'
            })
        
        return result
    
    def process_with_pipeline(self, files):
        """Override to initialize web progress tracking"""
        self.web_total_files = len(files)
        self.web_completed_files = 0
        
        # Update global state
        global extraction_state
        extraction_state["total_files"] = self.web_total_files
        extraction_state["completed_files"] = 0
        
        # Call parent method
        return super().process_with_pipeline(files)

def run_extraction_parallel(extractors_config, output_dir):
    """Run multiple extractors in parallel and write results immediately"""
    results = {}
    
    with ThreadPoolExecutor(max_workers=len(extractors_config)) as executor:
        # Submit all extraction tasks
        future_to_name = {
            executor.submit(extractor.run_extraction): name 
            for name, extractor in extractors_config.items()
        }
        
        # Collect results as they complete and write immediately
        for future in as_completed(future_to_name):
            extractor_name = future_to_name[future]
            try:
                result = future.result()
                results[extractor_name] = result
                logger.info(f"Completed {extractor_name} extraction")
                socketio.emit('analysis_log', {'message': f"Completed {extractor_name} extraction"})
                
                # Write result to file immediately
                if result:
                    write_results_to_file(extractor_name, result, output_dir)
                    
            except Exception as exc:
                logger.error(f"{extractor_name} extraction failed: {exc}")
                socketio.emit('analysis_log', {'message': f"{extractor_name} extraction failed: {exc}", 'type': 'error'})
                results[extractor_name] = None
    
    return results

def write_results_to_file(category_name, results, output_dir):
    """Write results to JSON file in the output directory"""
    try:
        filename = f"{category_name}.json"
        filepath = output_dir / filename
        
        results_data = results.model_dump()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results written to: {filepath}")
        socketio.emit('analysis_log', {'message': f"Results written to: {filename}"})
        return filepath
    except Exception as e:
        error_msg = f"Failed to write {category_name} results to file: {e}"
        logger.error(error_msg)
        socketio.emit('analysis_log', {'message': error_msg, 'type': 'error'})
        return None

def run_analysis():
    """Run the factfind analysis process directly (no subprocess)"""
    global analysis_state
    
    try:
        analysis_state["is_running"] = True
        analysis_state["current_stage"] = "Starting analysis"
        
        # Emit start event
        socketio.emit('analysis_started', {
            'message': 'Analysis started...',
            'stage': 'Initializing'
        })
        
        logger.info("Starting document extraction analysis")
        socketio.emit('analysis_log', {'message': 'Starting document extraction analysis'})
        
        # Ensure output directory exists
        output_dir = Path("output/result")
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        analysis_state["current_stage"] = "Running Batch 1"
        socketio.emit('analysis_progress', {
            'stage': 'BATCH 1: Basic, Asset, Liability',
            'message': 'Running parallel extraction'
        })
        
        # BATCH 1: basic_fact, asset, liability (concurrent)
        logger.info("BATCH 1: Running basic_fact, asset, and liability extractions in parallel...")
        socketio.emit('analysis_log', {'message': 'BATCH 1: Running basic_fact, asset, and liability extractions in parallel...'})
        
        batch1_extractors = {
            "basic_fact": BasicFactAnalyser(),
            "asset": AssetAnalyser(),
            "liability": LiabilityAnalyser()
        }
        
        batch1_results = run_extraction_parallel(batch1_extractors, output_dir)
        
        analysis_state["current_stage"] = "Running Batch 2"
        socketio.emit('analysis_progress', {
            'stage': 'BATCH 2: Income, Expense',
            'message': 'Running parallel extraction'
        })
        
        # BATCH 2: income, expense (concurrent)
        logger.info("BATCH 2: Running income and expense extractions in parallel...")
        socketio.emit('analysis_log', {'message': 'BATCH 2: Running income and expense extractions in parallel...'})
        
        batch2_extractors = {
            "income": IncomeAnalyser(),
            "expense": ExpenseAnalyser()
        }
        
        batch2_results = run_extraction_parallel(batch2_extractors, output_dir)
        
        analysis_state["is_running"] = False
        analysis_state["current_stage"] = "Complete"
        
        socketio.emit('analysis_complete', {
            'message': 'Analysis completed successfully!',
            'stage': 'Complete'
        })
        
        logger.info("All extractions completed successfully")
        socketio.emit('analysis_log', {'message': 'All extractions completed successfully'})
        
    except Exception as e:
        analysis_state["is_running"] = False
        analysis_state["current_stage"] = "Error"
        
        error_msg = f'Analysis failed: {str(e)}'
        socketio.emit('analysis_error', {
            'message': error_msg
        })
        socketio.emit('analysis_log', {'message': error_msg, 'type': 'error'})
        logger.error(f"Analysis failed: {e}")

def run_extraction():
    """Run the extraction process in background thread"""
    global extraction_state
    
    try:
        extraction_state["is_running"] = True
        extraction_state["error"] = None
        extraction_state["results"] = None
        
        # Initialize processor (copying from main function)
        max_concurrent = 10
        processor = WebFileProcessor(output_dir='./output/extraction', batch_size=max_concurrent)
        
        # Emit start event
        socketio.emit('extraction_started', {
            'message': 'Extraction started...',
            'max_concurrent': max_concurrent
        })
        
        # Run extraction
        results = processor.run()
        
        # Store results and mark as complete
        extraction_state["results"] = results
        extraction_state["is_running"] = False
        
        # Emit completion event
        socketio.emit('extraction_complete', {
            'message': 'Extraction completed!',
            'total_files': results['summary']['success'] + results['summary']['failed'],
            'successful': results['summary']['success'],
            'failed': results['summary']['failed']
        })
        
        logger.info(f"Extraction completed: {results['summary']['success']} successful, {results['summary']['failed']} failed")
        
        # Automatically start analysis if extraction was successful
        if results['summary']['success'] > 0:
            logger.info("Starting analysis automatically after successful extraction")
            time.sleep(1)  # Brief delay before starting analysis
            
            # Run analysis directly (no thread needed)
            run_analysis()
        
    except Exception as e:
        extraction_state["error"] = str(e)
        extraction_state["is_running"] = False
        
        socketio.emit('extraction_error', {
            'message': f'Extraction failed: {str(e)}'
        })
        
        logger.error(f"Extraction failed: {e}")

@app.route('/')
def index():
    """Main page with extraction interface"""
    return render_template('index.html')

@app.route('/start_extraction', methods=['POST'])
def start_extraction():
    """Start the extraction process"""
    global extraction_state
    
    if extraction_state["is_running"]:
        return jsonify({"error": "Extraction is already running"}), 400
    
    # Reset state
    extraction_state = {
        "is_running": True,
        "total_files": 0,
        "completed_files": 0,
        "current_file": "",
        "results": None,
        "error": None
    }
    
    # Start extraction in background thread
    thread = threading.Thread(target=run_extraction)
    thread.daemon = True
    thread.start()
    
    return jsonify({"message": "Extraction started"})

@app.route('/status')
def get_status():
    """Get current extraction status"""
    return jsonify(extraction_state)

@app.route('/analysis_status')
def get_analysis_status():
    """Get current analysis status"""
    return jsonify(analysis_state)

@app.route('/analysis_results')
def get_analysis_results():
    """Get all analysis results"""
    return jsonify(analysis_state["results"])

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status_update', extraction_state)
    emit('analysis_status_update', analysis_state)
    
    # Load and send existing analysis results
    existing_results = load_existing_analysis_results()
    for category, data in existing_results.items():
        if data is not None:
            emit('analysis_result', {
                'category': category,
                'data': data,
                'message': f'{category.replace("_", " ").title()} analysis loaded from file'
            })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    logger.info("Starting Web Extractor Interface")
    logger.info("Open your browser to http://localhost:5000")
    
    # Load existing analysis results on startup
    load_existing_analysis_results()
    logger.info("Loaded existing analysis results")
    
    # Start file watcher
    observer.start()
    logger.info("File watcher started for analysis results")
    
    try:
        # Run the Flask-SocketIO application
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    finally:
        observer.stop()
        observer.join()