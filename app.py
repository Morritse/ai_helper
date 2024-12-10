from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import PyPDF2
import io
import anthropic
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

app = Flask(__name__, static_url_path='/static')
# Configure CORS to allow requests from any origin
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize Anthropic client with API key
client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

# In-memory document store (Note: In production, use a proper database)
document_store = {}

def extract_text_from_pdf(pdf_content):
    """Extract text from PDF content"""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def fix_json_string(json_str):
    """Fix common JSON formatting issues"""
    json_str = re.search(r'\{.*\}', json_str, re.DOTALL).group(0)
    json_str = re.sub(r'(\d+|\btrue\b|\bfalse\b|\bnull\b|"[^"]*")\s+(?=["{\[]|[a-zA-Z])', r'\1,', json_str)
    json_str = re.sub(r'(\}|\]|\d+|"[^"]*")\s*\n\s*"', r'\1,\n"', json_str)
    json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)
    return json_str

def analyze_with_claude(text):
    """Send text to Claude for analysis"""
    try:
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
        
        response_text = message.content[0].text
        
        try:
            fixed_json = fix_json_string(response_text)
            json.loads(fixed_json)  # Validate JSON
            return fixed_json
        except Exception as e:
            print(f"Error fixing/validating JSON: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Error in Claude analysis: {str(e)}")
        return None

@app.route('/', methods=['GET', 'OPTIONS'])
def index():
    return send_file('index.html')

@app.route('/static/<path:path>', methods=['GET', 'OPTIONS'])
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_document():
    if request.method == 'OPTIONS':
        return '', 204
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    try:
        # Read the PDF file
        pdf_content = file.read()
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_content)
        print(f"Extracted text length: {len(text)}")
        
        # Generate document ID and store text
        doc_id = str(hash(text))
        document_store[doc_id] = text
        
        # Get analysis from Claude
        analysis = analyze_with_claude(text)
        
        if analysis:
            return jsonify({
                'analysis': analysis,
                'documentId': doc_id
            })
        else:
            return jsonify({'error': 'Failed to get properly formatted analysis from Claude'}), 500
            
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask():
    """Handle questions about the analyzed document"""
    if request.method == 'OPTIONS':
        return '', 204
        
    data = request.get_json()
    if not data or 'question' not in data or 'documentId' not in data:
        return jsonify({'error': 'Missing question or document ID'}), 400
    
    doc_id = data['documentId']
    if doc_id not in document_store:
        return jsonify({'error': 'Document not found. Please upload it again.'}), 404
    
    try:
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
        return jsonify({'answer': message.content[0].text})
    except Exception as e:
        print(f"Error asking question: {str(e)}")
        return jsonify({'error': 'Failed to get answer from Claude'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
