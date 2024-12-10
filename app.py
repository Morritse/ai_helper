from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import PyPDF2
import io
import anthropic
import os
from dotenv import load_dotenv
import json
import re
import logging
import sys
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def log_with_timestamp(message, level='info'):
    """Add timestamp and request ID to logs"""
    timestamp = datetime.now().isoformat()
    request_id = request.headers.get('X-Request-ID', 'NO_ID')
    log_message = f"[{timestamp}] [{request_id}] {message}"
    
    if level == 'error':
        logger.error(log_message)
    else:
        logger.info(log_message)

# Load environment variables
load_dotenv()

app = Flask(__name__, static_url_path='/static')
CORS(app)

# Initialize Anthropic client with API key
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    log_with_timestamp("ANTHROPIC_API_KEY not found in environment variables", 'error')
    raise ValueError("ANTHROPIC_API_KEY not found")

client = anthropic.Anthropic(api_key=api_key)

# In-memory document store
document_store = {}

def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        log_with_timestamp(f"Successfully extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        log_with_timestamp(f"Error extracting text from PDF: {str(e)}\n{traceback.format_exc()}", 'error')
        raise

def fix_json_string(json_str):
    """Fix common JSON formatting issues"""
    try:
        # Remove any text before the first { and after the last }
        json_str = re.search(r'\{.*\}', json_str, re.DOTALL).group(0)
        
        # Add missing commas between values in arrays and objects
        json_str = re.sub(r'(\d+|\btrue\b|\bfalse\b|\bnull\b|"[^"]*")\s+(?=["{\[]|[a-zA-Z])', r'\1,', json_str)
        
        # Add missing commas between object properties
        json_str = re.sub(r'(\}|\]|\d+|"[^"]*")\s*\n\s*"', r'\1,\n"', json_str)
        
        # Remove any trailing commas before closing brackets
        json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
        
        # Validate JSON
        json.loads(json_str)
        return json_str
    except Exception as e:
        log_with_timestamp(f"Error fixing JSON string: {str(e)}\n{traceback.format_exc()}", 'error')
        raise

def analyze_with_claude(text):
    """Send text to Claude for analysis"""
    try:
        log_with_timestamp("Starting Claude analysis")
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this financial document and provide:

1. Key financial metrics:
   - Extract and verify all numerical values
   - Convert text-based numbers to numerical format
   - Identify and standardize units (thousands, millions, etc.)

2. Financial health assessment:
   - Analyze current financial position
   - Compare against industry standards
   - Identify trends and patterns
   - Evaluate operational efficiency

3. Risk assessment:
   - Identify potential red flags
   - Analyze debt structure and obligations
   - Evaluate market and industry risks
   - Consider regulatory compliance issues

4. Strategic recommendations:
   - Provide actionable insights
   - Suggest areas for improvement
   - Recommend risk mitigation strategies
   - Outline potential growth opportunities

5. Creditworthiness evaluation:
   - Calculate key financial ratios
   - Compare to industry benchmarks
   - Consider qualitative factors
   - Provide a score from 0-100 with detailed justification

Format the response in JSON with the following structure:
{{
    "metrics": {{
        "revenue": number or null,
        "net_income": number or null,
        "total_assets": number or null,
        "total_liabilities": number or null,
        "cash_flow": number or null
    }},
    "health_assessment": "detailed assessment string",
    "risk_factors": ["list", "of", "risk", "factors"],
    "recommendations": ["list", "of", "recommendations"],
    "credit_score": number,
    "ratios": {{
        "debt_to_equity": number or null,
        "current_ratio": number or null,
        "quick_ratio": number or null
    }},
    "analysis_confidence": number
}}

Here's the document text:
{text}"""
                }
            ]
        )
        
        log_with_timestamp("Received response from Claude")
        response_text = message.content[0].text
        log_with_timestamp("Processing Claude response")
        
        try:
            fixed_json = fix_json_string(response_text)
            log_with_timestamp("Successfully processed Claude response")
            return fixed_json
        except Exception as e:
            log_with_timestamp(f"Error processing Claude response: {str(e)}\n{traceback.format_exc()}", 'error')
            return None
            
    except Exception as e:
        log_with_timestamp(f"Error in Claude analysis: {str(e)}\n{traceback.format_exc()}", 'error')
        return None

@app.route('/')
def index():
    try:
        return send_file('index.html')
    except Exception as e:
        log_with_timestamp(f"Error serving index.html: {str(e)}\n{traceback.format_exc()}", 'error')
        return jsonify({'error': 'Error serving page'}), 500

@app.route('/static/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('static', path)
    except Exception as e:
        log_with_timestamp(f"Error serving static file {path}: {str(e)}\n{traceback.format_exc()}", 'error')
        return jsonify({'error': 'Error serving static file'}), 500

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_document():
    if request.method == 'OPTIONS':
        return '', 204
        
    log_with_timestamp("Received analyze request")
    
    if 'file' not in request.files:
        log_with_timestamp("No file provided", 'error')
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        log_with_timestamp("No file selected", 'error')
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        log_with_timestamp("Invalid file type", 'error')
        return jsonify({'error': 'File must be a PDF'}), 400
    
    try:
        log_with_timestamp(f"Processing file: {file.filename}")
        # Read the PDF file
        pdf_content = file.read()
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_content)
        log_with_timestamp(f"Extracted text length: {len(text)}")
        
        # Generate document ID and store text
        doc_id = str(hash(text))
        document_store[doc_id] = text
        
        # Get analysis from Claude
        analysis = analyze_with_claude(text)
        
        if analysis:
            log_with_timestamp("Analysis completed successfully")
            return jsonify({
                'analysis': analysis,
                'documentId': doc_id
            })
        else:
            log_with_timestamp("Failed to get analysis from Claude", 'error')
            return jsonify({'error': 'Failed to get properly formatted analysis from Claude'}), 500
            
    except Exception as e:
        log_with_timestamp(f"Error processing document: {str(e)}\n{traceback.format_exc()}", 'error')
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask():
    """Handle questions about the analyzed document"""
    if request.method == 'OPTIONS':
        return '', 204
        
    log_with_timestamp("Received question request")
    
    try:
        data = request.get_json()
    except Exception as e:
        log_with_timestamp(f"Error parsing JSON request: {str(e)}\n{traceback.format_exc()}", 'error')
        return jsonify({'error': 'Invalid JSON'}), 400
    
    if not data or 'question' not in data or 'documentId' not in data:
        log_with_timestamp("Missing question or document ID", 'error')
        return jsonify({'error': 'Missing question or document ID'}), 400
    
    doc_id = data['documentId']
    if doc_id not in document_store:
        log_with_timestamp("Document not found", 'error')
        return jsonify({'error': 'Document not found. Please upload it again.'}), 404
    
    try:
        log_with_timestamp("Sending question to Claude")
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": f"""Here is a financial document text for context:

{document_store[doc_id]}

Answer this question about the document: {data['question']}

Provide a clear, concise answer based on the financial data. If the information isn't available in the document, say so."""
                }
            ]
        )
        log_with_timestamp("Received answer from Claude")
        return jsonify({'answer': message.content[0].text})
    except Exception as e:
        log_with_timestamp(f"Error asking question: {str(e)}\n{traceback.format_exc()}", 'error')
        return jsonify({'error': 'Failed to get answer from Claude'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
