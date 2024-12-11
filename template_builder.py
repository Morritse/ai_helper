from anthropic import Anthropic
import json
import os

def generate_template(description, metrics, visualizations):
    """Generate a template using Claude to structure the analysis based on user requirements"""
    
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # Ask Claude to help structure the analysis
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
    
    # Extract the JSON template from Claude's response
    response_text = message.content[0].text
    template_json = json.loads(response_text)
    
    return template_json

def validate_template(template):
    """Validate that the template has all required fields and proper structure"""
    required_fields = ['name', 'description', 'prompt_template', 'visualization']
    
    for field in required_fields:
        if field not in template:
            raise ValueError(f"Missing required field: {field}")
            
    if not isinstance(template['visualization'], dict):
        raise ValueError("Visualization must be a dictionary")
        
    for viz_name, viz_config in template['visualization'].items():
        if 'type' not in viz_config:
            raise ValueError(f"Visualization {viz_name} missing 'type'")
        if 'fields' not in viz_config:
            raise ValueError(f"Visualization {viz_name} missing 'fields'")
            
    return True

def save_template(template, template_id):
    """Save a template to the templates directory"""
    template_path = f"config/templates/{template_id}.json"
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    
    with open(template_path, 'w') as f:
        json.dump(template, f, indent=4)
        
    return template_path

def create_custom_template(description, metrics, visualizations):
    """Create a custom template based on user requirements"""
    try:
        # Generate template using Claude
        template = generate_template(description, metrics, visualizations)
        
        # Validate template structure
        validate_template(template)
        
        # Generate template ID from name
        template_id = template['name'].lower().replace(' ', '_')
        
        # Save template
        template_path = save_template(template, template_id)
        
        return {
            'success': True,
            'template_id': template_id,
            'template': template,
            'path': template_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Example usage:
if __name__ == "__main__":
    # Example inputs
    description = """
    This is a medical device performance report that includes:
    - Device usage statistics
    - Error rates and types
    - Patient outcomes
    - Maintenance records
    """
    
    metrics = """
    Please extract:
    1. Total devices deployed
    2. Average usage hours
    3. Error frequency
    4. Patient satisfaction scores
    5. Maintenance costs
    6. Performance trends
    """
    
    visualizations = """
    I would like:
    1. Bar chart showing error rates by type
    2. Line graph of usage over time
    3. Gauge chart for patient satisfaction
    4. Radar chart comparing different performance metrics
    """
    
    result = create_custom_template(description, metrics, visualizations)
    print(json.dumps(result, indent=2))
