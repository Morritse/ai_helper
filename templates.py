# Templates are stored directly in code for serverless deployment
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
    },
    "medical": {
        "name": "Medical Research Analysis",
        "description": "Analyze medical research papers and clinical studies",
        "prompt_template": """Analyze this medical research paper and provide:

1. Study Overview:
   - Research objective/hypothesis
   - Study design and methodology
   - Population characteristics
   - Time period and location

2. Statistical Analysis:
   - Sample size and demographics
   - Primary outcomes measured
   - Statistical methods used
   - P-values and confidence intervals
   - Effect sizes

3. Results Assessment:
   - Key findings
   - Statistical significance
   - Clinical significance
   - Limitations identified
   - Potential biases

4. Clinical Implications:
   - Practice recommendations
   - Population applicability
   - Implementation considerations
   - Required resources

5. Quality Evaluation:
   - Methodology strength (score 0-100)
   - Evidence quality (score 0-100)
   - Bias risk assessment (score 0-100)
   - Overall study quality (score 0-100)

Format the response in JSON with the following structure:
{
    "overview": {
        "objective": "text",
        "design": "text",
        "population": "text",
        "timeframe": "text"
    },
    "statistics": {
        "sample_size": "number",
        "outcomes": ["list of outcomes"],
        "methods": ["list of methods"],
        "p_values": ["list of significant p-values"],
        "effect_sizes": ["list of effect sizes"]
    },
    "results": {
        "findings": ["list of key findings"],
        "statistical_significance": "text",
        "clinical_significance": "text",
        "limitations": ["list of limitations"],
        "biases": ["list of potential biases"]
    },
    "implications": {
        "recommendations": ["list of recommendations"],
        "applicability": "text",
        "implementation": ["list of considerations"],
        "resources": ["list of required resources"]
    },
    "quality": {
        "methodology_score": "number 0-100",
        "evidence_score": "number 0-100",
        "bias_risk_score": "number 0-100",
        "overall_score": "number 0-100"
    }
}""",
        "visualization": {
            "quality_scores": {
                "type": "radar",
                "fields": ["quality.methodology_score", "quality.evidence_score", "quality.bias_risk_score", "quality.overall_score"],
                "title": "Study Quality Assessment"
            },
            "overall_quality": {
                "type": "gauge",
                "field": "quality.overall_score",
                "title": "Overall Study Quality",
                "min": 0,
                "max": 100
            }
        }
    }
}
