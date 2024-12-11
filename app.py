from flask import Flask, request, jsonify
import json
import os
import uuid
from werkzeug.utils import secure_filename
import PyPDF2
import openai

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load templates from config files
def load_templates():
    templates = []
    template_dir = os.path.join('config', 'templates')
    if os.path.exists(template_dir):
        for filename in os.listdir(template_dir):
            if filename.endswith('.json'):
                with open(os.path.join(template_dir, filename)) as f:
                    template = json.load(f)
                    templates.append(template)
    return templates

@app.route('/templates', methods=['GET'])
def get_templates():
    templates = load_templates()
    return jsonify({'templates': templates})

@app.route('/create_template', methods=['POST'])
def create_template():
    data = request.json
    template_id = str(uuid.uuid4())
    
    template = {
        'id': template_id,
        'name': data['name'],
        'description': data['description'],
        'metrics': data['metrics'].split('\n'),
        'visualizations': {
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
    
    # Save template
    os.makedirs(os.path.join('config', 'templates'), exist_ok=True)
    with open(os.path.join('config', 'templates', f'{template_id}.json'), 'w') as f:
        json.dump(template, f, indent=2)
    
    return jsonify({
        'template_id': template_id,
        'template': template
    })

@app.route('/analyze', methods=['POST'])
def analyze_document():
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
        
        # Analyze text using OpenAI
        analysis_prompt = f"""
        Analyze the following financial document text and extract key metrics:
        {text[:4000]}  # Limit text length for API
        
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
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst. Analyze the document and return metrics as JSON."},
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        analysis = response.choices[0].message.content
        
        # Store analysis for later Q&A
        document_id = str(uuid.uuid4())
        with open(os.path.join(app.config['UPLOAD_FOLDER'], f'{document_id}.txt'), 'w') as f:
            f.write(text)
        
        return jsonify({
            'documentId': document_id,
            'analysis': analysis,
            'template': load_template_by_id(template_id)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    document_id = data.get('documentId')
    
    if not question or not document_id:
        return jsonify({'error': 'Question and document ID are required'}), 400
    
    try:
        # Get document text
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{document_id}.txt')
        if not os.path.exists(filepath):
            return jsonify({'error': 'Document not found'}), 404
            
        with open(filepath) as f:
            text = f.read()
        
        # Use OpenAI to answer question
        prompt = f"""
        Based on this document:
        {text[:4000]}
        
        Answer this question:
        {question}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst assistant. Answer questions about the document."},
                {"role": "user", "content": prompt}
            ]
        )
        
        answer = response.choices[0].message.content
        return jsonify({'answer': answer})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def load_template_by_id(template_id):
    template_path = os.path.join('config', 'templates', f'{template_id}.json')
    if os.path.exists(template_path):
        with open(template_path) as f:
            return json.load(f)
    return None

if __name__ == '__main__':
    app.run(debug=True)
