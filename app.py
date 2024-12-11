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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
CORS(app)

# Initialize Anthropic client with API key from environment variable
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    logger.error("ANTHROPIC_API_KEY not found in environment variables")
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

client = anthropic.Anthropic(api_key=api_key)
logger.info("Initialized Anthropic client")

# Built-in templates
TEMPLATES = {
    "financial": {
        "name": "Financial Analysis",
        "description": "Analyze financial documents and statements",
        "prompt_template": """Analyze this financial document and provide:

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
{
    "metrics": {
        "revenue": number or null,
        "net_income": number or null,
        "total_assets": number or null,
        "total_liabilities": number or null,
        "cash_flow": number or null
    },
    "health_assessment": "detailed assessment string",
    "risk_factors": ["list", "of", "risk", "factors"],
    "recommendations": ["list", "of", "recommendations"],
    "credit_score": number,
    "ratios": {
        "debt_to_equity": number or null,
        "current_ratio": number or null,
        "quick_ratio": number or null
    },
    "analysis_confidence": number
}""",
        "visualization": {
            "metrics": {
                "type": "bar",
                "fields": ["revenue", "net_income", "cash_flow"],
                "title": "Key Financial Metrics",
                "unit": "millions"
            },
            "ratios": {
                "type": "radar",
                "fields": ["debt_to_equity", "current_ratio", "quick_ratio"],
                "title": "Financial Ratios Analysis"
            },
            "score": {
                "type": "gauge",
                "field": "credit_score",
                "title": "Credit Score",
                "min": 0,
                "max": 100
            }
        }
    },
    "legal": {
        "name": "Legal Document Analysis",
        "description": "Analyze legal documents, contracts, and agreements",
        "prompt_template": """Analyze this legal document and provide:

1. Document Classification:
   - Document type and purpose
   - Jurisdiction and governing law
   - Parties involved
   - Effective date and duration

2. Key Terms Analysis:
   - Main obligations and rights
   - Critical deadlines and dates
   - Payment terms and conditions
   - Termination clauses

3. Risk Assessment:
   - Potential legal risks
   - Compliance requirements
   - Liability exposure
   - Dispute resolution mechanisms

4. Recommendations:
   - Areas requiring attention
   - Suggested modifications
   - Compliance measures
   - Risk mitigation strategies

5. Overall Evaluation:
   - Document completeness
   - Legal enforceability
   - Risk level assessment
   - Provide a score from 0-100 with justification

Format the response in JSON with the following structure:
{
    "classification": {
        "type": "string",
        "jurisdiction": "string",
        "parties": ["list of parties"],
        "effective_date": "date string",
        "duration": "string"
    },
    "key_terms": {
        "obligations": ["list of obligations"],
        "deadlines": ["list of deadlines"],
        "payment_terms": "string",
        "termination_clauses": ["list of clauses"]
    },
    "risks": {
        "legal_risks": ["list of risks"],
        "compliance_requirements": ["list of requirements"],
        "liability_concerns": ["list of concerns"]
    },
    "recommendations": ["list of recommendations"],
    "evaluation": {
        "completeness_score": "number 0-100",
        "enforceability_score": "number 0-100",
        "risk_level": "string (Low/Medium/High)",
        "overall_score": "number 0-100"
    }
}""",
        "visualization": {
            "scores": {
                "type": "radar",
                "fields": ["evaluation.completeness_score", "evaluation.enforceability_score", "evaluation.overall_score"],
                "title": "Document Quality Scores"
            },
            "risk_level": {
                "type": "gauge",
                "field": "evaluation.overall_score",
                "title": "Overall Risk Level",
                "min": 0,
                "max": 100
            }
        }
    }
}

# In-memory document store
document_store = {}

# In-memory custom templates store
custom_templates = {}

@app.route('/templates', methods=['GET'])
def list_templates():
    """List available analysis templates"""
    all_templates = {**TEMPLATES, **custom_templates}
    return jsonify({
        'templates': [
            {
                'id': template_id,
                'name': template['name'],
                'description': template['description']
            }
            for template_id, template in all_templates.items()
        ]
    })

@app.route('/create_template', methods=['POST'])
def create_template():
    """Create a custom template based on user requirements"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        description = data.get('description')
        metrics = data.get('metrics')
        visualizations = data.get('visualizations')
        
        if not all([description, metrics, visualizations]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Generate template using Claude
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Help me create a document analysis template.

Document Description:
{description}

Metrics/Data to Extract:
{metrics}

Desired Visualizations:
{visualizations}

Create a template that includes:
1. A structured prompt for analyzing such documents
2. A JSON schema for the response format
3. Visualization configuration

Format the response as a JSON object with these fields:
{{
    "name": "Template name based on document type",
    "description": "Brief description of what this template analyzes",
    "prompt_template": "The full prompt with clear instructions and sections",
    "visualization": {{
        Visualization configuration matching the desired charts/graphs
    }}
}}

Make the prompt very specific about:
- What information to extract
- How to format numbers and text
- What patterns to look for
- How to structure the analysis

The visualization config should specify:
- Chart types (bar, radar, gauge, etc.)
- Which fields to display
- Titles and labels
- Units and ranges where applicable"""
            }]
        )
        
        template = json.loads(message.content[0].text)
        template_id = template['name'].lower().replace(' ', '_')
        
        # Store template
        custom_templates[template_id] = template
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'template': template
        })
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Failed to create template'}), 500

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
            
        template_id = request.form.get('template', 'financial')  # Default to financial template
        
        # Check both built-in and custom templates
        all_templates = {**TEMPLATES, **custom_templates}
        if template_id not in all_templates:
            logger.error(f"Invalid template: {template_id}")
            return jsonify({'error': 'Invalid template'}), 400
            
        template = all_templates[template_id]
        logger.info(f"Using template: {template_id}")
        
        file = request.files['file']
        logger.info(f"Received file: {file.filename}")
        
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.pdf'):
            logger.error("Invalid file type")
            return jsonify({'error': 'File must be a PDF'}), 400
        
        # Read the PDF file
        pdf_content = file.read()
        logger.info(f"Read {len(pdf_content)} bytes from file")
        
        # Extract text from PDF
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            logger.info(f"Extracted {len(text)} characters from PDF")
            
            if len(text.strip()) == 0:
                logger.error("No text extracted from PDF")
                return jsonify({'error': 'Could not extract text from PDF'}), 400
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': 'Failed to read PDF file'}), 400
        
        # Generate document ID and store text
        doc_id = str(hash(text))
        document_store[doc_id] = {
            'text': text,
            'template_id': template_id
        }
        logger.info(f"Stored document with ID: {doc_id}")
        
        # Get analysis from Claude
        try:
            logger.info("Sending text to Claude for analysis")
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"{template['prompt_template']}\n\nHere's the document text:\n{text}"
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
                analysis = json.loads(json_str)
                logger.info("Successfully processed and validated JSON response")
                
                return jsonify({
                    'analysis': json_str,
                    'documentId': doc_id,
                    'template': {
                        'id': template_id,
                        'visualization': template['visualization']
                    }
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
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"""Here is a document text for context:

{document_store[doc_id]['text']}

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
