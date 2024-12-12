# Financial Document Analyzer

A web application that analyzes financial documents in PDF format and assesses the creditworthiness of companies based on metrics in the reports. The application uses Claude AI to extract and analyze financial data, providing detailed insights, recommendations, and allowing users to ask questions about the analyzed documents.

## Features

- PDF document upload and analysis
- Key financial metrics extraction
- Financial health assessment
- Risk factor analysis
- Strategic recommendations
- Creditworthiness evaluation
- Interactive Q&A about the analyzed document
- Visual representation of financial data through charts

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python with Flask
- AI: Anthropic's Claude API
- PDF Processing: PyPDF2
- Charts: Chart.js
- Deployment: Vercel

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/financial-document-analyzer.git
cd financial-document-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory and add:
```
ANTHROPIC_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python app.py
```

## Usage

1. Upload a financial document (PDF format)
2. View the automated analysis including:
   - Key financial metrics
   - Financial health assessment
   - Risk factors
   - Recommendations
   - Credit score
3. Ask questions about the document using the chat interface

## Project Structure

```
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── static/            
│   └── css/           
│       └── styles.css  # Application styles
├── templates/         
│   └── index.html     # Main HTML template
└── vercel.json        # Vercel deployment configuration
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
