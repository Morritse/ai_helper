from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import PyPDF2
import io
import anthropic
import os
import json
import re
import logging
import sys
import traceback
import pandas as pd
import docx2txt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
CORS(app)

# Initialize Anthropic client
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    logger.error("ANTHROPIC_API_KEY not found in environment variables")
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

client = anthropic.Anthropic()
logger.info("Initialized Anthropic client")

# In-memory document store
document_store = {}

def extract_text_from_pdf(file_content):
    """Extract text from PDF file"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_txt(file_content):
    """Extract text from TXT file"""
    return file_content.decode('utf-8')

def extract_text_from_csv(file_content):
    """Extract text from CSV file and convert to structured text"""
    df = pd.read_csv(io.BytesIO(file_content))
    # Convert DataFrame to a structured string representation
    return df.to_string()

def extract_text_from_docx(file_content):
    """Extract text from DOCX file"""
    return docx2txt.process(io.BytesIO(file_content))

# Document type handlers
DOCUMENT_HANDLERS = {
    '.pdf': extract_text_from_pdf,
    '.txt': extract_text_from_txt,
    '.csv': extract_text_from_csv,
    '.docx': extract_text_from_docx
}

# Analysis prompts for different document types
ANALYSIS_PROMPTS = {
    '.pdf': """Analyze this financial document and provide:
    [Previous PDF analysis prompt]""",
    
    '.csv': """Analyze this CSV data and provide:
    1. Data Overview:
       - Number of records
       - Key columns identified
       - Data quality assessment
    
    2. Statistical Analysis:
       - Summary statistics
       - Key trends
       - Notable patterns
    
    3. Financial Metrics:
       - Calculate relevant financial ratios
       - Identify key performance indicators
       - Track changes over time
    
    4. Recommendations:
       - Data-driven insights
       - Areas for improvement
       - Action items
    
    Format as JSON with structure:
    {
        "data_overview": {
            "record_count": number,
            "columns": [string],
            "quality_score": number
        },
        "statistics": {
            "summary": object,
            "trends": [string],
            "patterns": [string]
        },
        "metrics": {
            "ratios": object,
            "kpis": object
        },
        "recommendations": [string]
    }""",
    
    '.txt': """Analyze this text document and provide:
    1. Content Analysis:
       - Main topics
       - Key points
       - Important dates/numbers
    
    2. Financial Information:
       - Extract monetary values
       - Identify financial terms
       - Find relevant dates
    
    3. Risk Assessment:
       - Potential issues
       - Areas of concern
       - Compliance matters
    
    4. Action Items:
       - Required steps
       - Follow-up tasks
       - Recommendations
    
    Format as JSON with structure:
    {
        "content": {
            "topics": [string],
            "key_points": [string],
            "important_data": object
        },
        "financial_info": {
            "monetary_values": object,
            "terms": [string],
            "dates": [string]
        },
        "risks": {
            "issues": [string],
            "concerns": [string],
            "compliance": [string]
        },
        "actions": [string]
    }""",
    
    '.docx': """Analyze this document and provide:
    1. Document Structure:
       - Sections identified
       - Key headings
       - Important paragraphs
    
    2. Content Analysis:
       - Main points
       - Critical information
       - Supporting details
    
    3. Financial Data:
       - Monetary values
       - Financial terms
       - Calculations
    
    4. Recommendations:
       - Key takeaways
       - Action items
       - Follow-up steps
    
    Format as JSON with structure:
    {
        "structure": {
            "sections": [string],
            "headings": [string],
            "key_paragraphs": [string]
        },
        "content": {
            "main_points": [string],
            "critical_info": object,
            "details": [string]
        },
        "financial": {
            "values": object,
            "terms": [string],
            "calculations": object
        },
        "recommendations": [string]
    }"""
}

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_document():
    if request.method == 'OPTIONS':
        return '', 204
        
    logger.info("Received analyze request")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    try:
        if 'file' not in request.files:
            logger.error("No file provided in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        logger.info(f"Received file: {file.filename}")
        
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        # Get file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in DOCUMENT_HANDLERS:
            logger.error(f"Unsupported file type: {file_ext}")
            return jsonify({'error': f'Unsupported file type. Supported types: {", ".join(DOCUMENT_HANDLERS.keys())}'}, 400)
        
        # Read and extract text from file
        file_content = file.read()
        try:
            text = DOCUMENT_HANDLERS[file_ext](file_content)
            logger.info(f"Extracted {len(text)} characters from {file_ext} file")
            
            if len(text.strip()) == 0:
                logger.error("No text extracted from file")
                return jsonify({'error': 'Could not extract text from file'}), 400
                
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Failed to read {file_ext} file'}), 400
        
        # Generate document ID and store text
        doc_id = str(hash(text))
        document_store[doc_id] = text
        logger.info(f"Stored document with ID: {doc_id}")
        
        # Get analysis from Claude
        try:
            logger.info("Sending text to Claude for analysis")
            message = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": ANALYSIS_PROMPTS[file_ext] + f"\n\nHere's the document text:\n{text}"
                }]
            )
            
            logger.info("Received response from Claude")
            response_text = message.content[0].text
            
            # Fix and validate JSON
            try:
                json_str = re.search(r'\{.*\}', response_text, re.DOTALL).group(0)
                json_str = re.sub(r'(\d+|\btrue\b|\bfalse\b|\bnull\b|"[^"]*")\s+(?=["{\[]|[a-zA-Z])', r'\1,', json_str)
                json_str = re.sub(r'(\}|\]|\d+|"[^"]*")\s*\n\s*"', r'\1,\n"', json_str)
                json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
                
                # Validate JSON
                json.loads(json_str)
                logger.info("Successfully processed and validated JSON response")
                
                return jsonify({
                    'analysis': json_str,
                    'documentId': doc_id
                })
            except Exception as e:
                logger.error(f"Error processing Claude response: {str(e)}\n{traceback.format_exc()}")
                return jsonify({'error': 'Failed to process analysis results'}), 500
                
        except Exception as e:
            logger.error(f"Error getting analysis from Claude: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Failed to analyze document'}), 500
            
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask():
    """Handle questions about the analyzed document"""
    if request.method == 'OPTIONS':
        return '', 204
        
    logger.info("Received question request")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request body: {request.get_json()}")
    
    try:
        data = request.get_json()
    except Exception as e:
        logger.error(f"Error parsing JSON request: {str(e)}")
        return jsonify({'error': 'Invalid JSON'}), 400
    
    if not data or 'question' not in data or 'documentId' not in data:
        logger.error("Missing question or document ID")
        return jsonify({'error': 'Missing question or document ID'}), 400
    
    doc_id = data['documentId']
    if doc_id not in document_store:
        logger.error(f"Document not found: {doc_id}")
        return jsonify({'error': 'Document not found. Please upload it again.'}), 404
    
    try:
        logger.info("Sending question to Claude")
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Here is a document text for context:

{document_store[doc_id]}

Answer this question about the document: {data['question']}

Provide a clear, concise answer based on the document content. If the information isn't available in the document, say so."""
            }]
        )
        logger.info("Received answer from Claude")
        return jsonify({'answer': message.content[0].text})
    except Exception as e:
        logger.error(f"Error asking question: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Failed to get answer from Claude'}), 500

@app.route('/')
def index():
    try:
        return send_file('index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Error serving page'}), 500

@app.route('/static/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('static', path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Error serving static file'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
