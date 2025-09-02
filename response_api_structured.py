#!/usr/bin/env python3
"""
Test script using OpenAI Responses API to analyze trans.pdf
Following the example pattern for structured JSON output
"""
from openai import OpenAI
from pydantic import BaseModel
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("apikey"))  # Using same env var as other scripts

class Summary(BaseModel):
    summary: str
    # this must be added to actually make openai api work
    class Config:
        extra = "forbid"


def analyze_trans_pdf():
    """Analyze trans.pdf using OpenAI Responses API with structured output"""
    
    # Check if trans.pdf exists
    pdf_path = Path("trans.pdf")
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return None
    
    print(f"📄 Analyzing file: {pdf_path}")
    
    try:
        # 1. Upload the PDF
        print("⬆️ Uploading PDF to OpenAI...")
        file = client.files.create(
            file=open("trans.pdf", "rb"),
            purpose="user_data"
        )
        print(f"✅ File uploaded with ID: {file.id}")
        
    
        # 3. Send Responses API request with structured output
        print("🔍 Analyzing document with structured extraction...")
        response = client.responses.parse(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user", 
                    "content": [
                        {"type": "input_file", "file_id": file.id},
                        {"type": "input_text", "text": """
                        summarise doc
                        """}
                    ]
                }
            ],
            text_format=Summary,
        )
        
        # 4. Retrieve and process the structured JSON
        print("📊 Processing extracted data...")
        print(response.output_parsed)
        
            
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return None

def main():
    """Main function"""
    print("🚀 Starting trans.pdf analysis using OpenAI Responses API")
    
    analyze_trans_pdf()
    
   
if __name__ == "__main__":
    main()