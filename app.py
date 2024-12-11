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
                "content": f"""Create a document analysis template based on these requirements:

Document Description:
{description}

Metrics to Extract:
{metrics}

Desired Visualizations:
{visualizations}

Return ONLY a JSON object with this structure:
{{
    "name": "Name based on document type",
    "description": "Brief description of analysis purpose",
    "prompt_template": {{
        "instructions": "Main analysis instructions",
        "sections": [
            {{
                "section": "Section name",
                "instructions": ["List", "of", "specific", "instructions"]
            }}
        ],
        "output_format": {{
            Define expected JSON structure for the analysis output
        }}
    }},
    "visualization": {{
        "primary_chart": {{
            "type": "chart type (bar/line/pie/etc)",
            "config": {{
                "title": "Chart title",
                "xAxis": {{ "type": "category", "title": "X-axis label" }},
                "yAxis": {{ "type": "value", "title": "Y-axis label" }},
                "series": [
                    {{
                        "name": "Series name",
                        "type": "chart type",
                        "color": "hex color"
                    }}
                ]
            }}
        }},
        "secondary_charts": [
            {{
                "type": "chart type",
                "config": {{
                    Chart specific configuration
                }}
            }}
        ]
    }}
}}

Make the template specific to the document type and metrics requested. Include clear instructions for data extraction and formatting."""
            }]
        )
        
        # Extract and validate JSON from response
        try:
            response_text = message.content[0].text
            # Find JSON object in response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise ValueError("No JSON found in response")
                
            template = json.loads(json_match.group(0))
            
            # Basic validation
            required_fields = ['name', 'description', 'prompt_template', 'visualization']
            if not all(field in template for field in required_fields):
                raise ValueError("Missing required fields in template")
                
            template_id = template['name'].lower().replace(' ', '_')
            
            # Store template
            custom_templates[template_id] = template
            
            return jsonify({
                'success': True,
                'template_id': template_id,
                'template': template
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}\nResponse text: {response_text}")
            return jsonify({'error': 'Invalid JSON in template response'}), 500
        except Exception as e:
            logger.error(f"Template processing error: {str(e)}")
            return jsonify({'error': 'Failed to process template'}), 500
            
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Failed to create template'}), 500

# Rest of the code remains the same...
