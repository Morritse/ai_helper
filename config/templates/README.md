# Template Configuration Guide

Each template is a JSON file that tells the system:
1. How to analyze documents
2. What data to extract
3. How to visualize results

## Template Structure

```json
{
    "name": "Template Name",
    "description": "Brief description of what this template analyzes",
    
    "prompt_template": "Instructions for Claude",
    
    "visualization": {
        "chart configurations"
    }
}
```

## Writing Instructions for Claude

The `prompt_template` should:
1. Be clearly structured with numbered sections
2. Use bullet points for specific instructions
3. Include exact formatting requirements
4. Specify units and ranges for numbers

Example structure:
```
Analyze this document and provide:

1. Section Name:
   - What to look for
   - How to process it
   - Expected format

2. Another Section:
   - Be specific about units (thousands, millions, etc.)
   - Specify ranges (0-100, positive/negative)
   - Define terms if needed

Format the response in JSON with the following structure:
{
    "section_name": {
        "field1": "type (number/text/list)",
        "field2": "type with range or format"
    }
}
```

## Visualization Types

Available chart types:
- `bar`: For comparing numerical values
- `radar`: For showing multiple metrics
- `gauge`: For displaying scores/ranges
- `timeline`: For date-based data

Example visualization config:
```json
"visualization": {
    "chart_name": {
        "type": "bar",
        "fields": ["field1", "field2"],
        "title": "Chart Title",
        "unit": "optional unit"
    },
    "score_display": {
        "type": "gauge",
        "field": "score_field",
        "title": "Score Title",
        "min": 0,
        "max": 100
    }
}
```

## Tips for Good Templates

1. Clear Instructions:
   - Be specific about what to extract
   - Define how to handle edge cases
   - Specify units and formats

2. Structured Data:
   - Use consistent field names
   - Define clear data types
   - Group related fields together

3. Useful Visualizations:
   - Choose appropriate chart types
   - Group related metrics
   - Consider data ranges

## Example Fields

Common field types:
```json
{
    "text_field": "string",
    "number_field": "number",
    "score": "number 0-100",
    "date": "YYYY-MM-DD",
    "list": ["array", "of", "items"],
    "nested": {
        "subfield": "value"
    }
}
```

## Testing Templates

1. Start with a sample document
2. Check if Claude's response matches your JSON structure
3. Verify visualizations display correctly
4. Test edge cases (missing data, unusual values)

## Common Issues

1. JSON Formatting:
   - Missing quotes around field names
   - Trailing commas
   - Unescaped quotes in strings

2. Visualization:
   - Field names don't match JSON structure
   - Data types don't match expected format
   - Ranges not properly specified

3. Instructions:
   - Ambiguous requirements
   - Missing format specifications
   - Unclear units or ranges
