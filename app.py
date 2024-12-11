from flask import Flask, request, jsonify, send_file, send_from_directory, render_template
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
from templates import TEMPLATES
from template_builder import create_custom_template

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

# In-memory document store
document_store = {}

@app.route('/builder')
def template_builder():
    """Serve the template builder page"""
    try:
        return send_file('templates/builder.html')
    except Exception as e:
        logger.error(f"Error serving builder.html: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Error serving page'}), 500

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
            
        result = create_custom_template(description, metrics, visualizations)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Failed to create template'}), 500

@app.route('/save_template', methods=['POST'])
def save_template():
    """Save a custom template"""
    try:
        template = request.get_json()
        if not template:
            return jsonify({'error': 'No template provided'}), 400
            
        template_id = template['name'].lower().replace(' ', '_')
        
        # Add to TEMPLATES dictionary
        TEMPLATES[template_id] = template
        
        return jsonify({
            'success': True,
            'template_id': template_id
        })
        
    except Exception as e:
        logger.error(f"Error saving template: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Failed to save template'}), 500

@app.route('/templates', methods=['GET'])
def list_templates():
    """List available analysis templates"""
    return jsonify({
        'templates': [
            {
                'id': template_id,
                'name': template['name'],
                'description': template['description']
            }
            for template_id, template in TEMPLATES.items()
        ]
    })

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
        if template_id not in TEMPLATES:
            logger.error(f"Invalid template: {template_id}")
            return jsonify({'error': 'Invalid template'}), 400
            
        template = TEMPLATES[template_id]
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
