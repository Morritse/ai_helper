from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
from werkzeug.utils import secure_filename
import PyPDF2
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Claude
claude = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
if not os.getenv('ANTHROPIC_API_KEY'):
    print("Warning: ANTHROPIC_API_KEY not set")

# Default template
DEFAULT_TEMPLATE = {
    "id": "financial-default",
    "name": "Financial Report Analysis",
    "description": "Analyzes financial reports to extract key metrics and assess company health",
    "metrics": [
        "Revenue",
        "Net Income",
        "Operating Cash Flow",
        "Total Assets",
        "Liquidity Ratio",
        "Profitability Ratio",
        "Efficiency Ratio",
        "Solvency Ratio"
    ],
    "visualization": {
        "financial_health": {
            "type": "radar",
            "title": "Financial Health Indicators",
            "fields": ["liquidity", "profitability", "efficiency", "solvency"]
        },
        "key_metrics": {
            "type": "bar",
            "title": "Key Financial Metrics",
            "fields": ["revenue", "net_income", "operating_cash_flow", "total_assets"]
        }
    }
}

@app.route('/templates', methods=['GET'])
def get_templates():
    try:
        # Return default template
        return jsonify({'templates': [DEFAULT_TEMPLATE]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_template', methods=['POST', 'OPTIONS'])
def create_template():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.json
        template_id = str(uuid.uuid4())
        
        template = {
            'id': template_id,
            'name': data['name'],
            'description': data['description'],
            'metrics': data['metrics'].split('\n'),
            'visualization': {
                'financial_health': {
                    'type': 'radar',
                    'title': 'Financial Health Indicators',
                    'fields': ['liquidity', 'profitability', 'efficiency', 'solvency']
                },
                'key_metrics': {
                    'type': 'bar',
                    'title': 'Key Financial Metrics',
                    'fields': ['revenue', 'net_income', 'operating_cash_flow', 'total_assets']
                }
            }
        }
        
        return jsonify({
            'template_id': template_id,
            'template': template
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_document():
    if request.method == 'OPTIONS':
        return '', 204
        
    if not os.getenv('ANTHROPIC_API_KEY'):
        return jsonify({'error': 'Claude API key not configured'}), 500
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    template_id = request.form.get('template')
    if not template_id:
        return jsonify({'error': 'No template specified'}), 400
    
    # Save and process PDF
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Extract text from PDF
        with open(filepath, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        
        # Analyze text using Claude
        analysis_prompt = f"""
        Analyze the following financial document text and extract key metrics:
        {text[:10000]}  # Claude can handle more text than GPT
        
        Return the analysis as a JSON object with these fields:
        - liquidity
        - profitability
        - efficiency
        - solvency
        - revenue
        - net_income
        - operating_cash_flow
        - total_assets
        
        Each field should be a number between 0 and 100.
        
        Format your response as valid JSON only, with no additional text.
        """
        
        response = claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )
        
        analysis = response.content[0].text
        
        # Store analysis for later Q&A
        document_id = str(uuid.uuid4())
        with open(os.path.join(app.config['UPLOAD_FOLDER'], f'{document_id}.txt'), 'w') as f:
            f.write(text)
        
        return jsonify({
            'documentId': document_id,
            'analysis': analysis,
            'template': DEFAULT_TEMPLATE
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/ask', methods=['POST', 'OPTIONS'])
def ask_question():
    if request.method == 'OPTIONS':
        return '', 204
        
    if not os.getenv('ANTHROPIC_API_KEY'):
        return jsonify({'error': 'Claude API key not configured'}), 500
        
    try:
        data = request.json
        question = data.get('question')
        document_id = data.get('documentId')
        
        if not question or not document_id:
            return jsonify({'error': 'Question and document ID are required'}), 400
        
        # Get document text
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{document_id}.txt')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Document not found'}), 404
            
        with open(filepath) as f:
            text = f.read()
        
        # Use Claude to answer question
        prompt = f"""
        Based on this document:
        {text[:10000]}
        
        Answer this question:
        {question}
        
        Provide a clear and concise answer based only on the information in the document.
        """
        
        response = claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        answer = response.content[0].text
        return jsonify({'answer': answer})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
