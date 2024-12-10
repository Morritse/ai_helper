# Financial Document Analyzer

A web application that analyzes financial documents using Claude AI to assess creditworthiness and provide financial insights.

## Features

- PDF document analysis
- Key financial metrics extraction
- Financial health assessment
- Risk analysis
- Credit scoring
- Interactive Q&A about the document
- Visual charts and graphs
- Real-time analysis

## Deployment to Vercel

1. Install Vercel CLI (use sudo for global installation):
```bash
sudo npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Initialize Git repository (if not already done):
```bash
git init
git add .
git commit -m "Initial commit"
```

4. Deploy the application:
```bash
vercel
```
When prompted:
- Set up and deploy: Yes
- Link to existing project: No
- Project name: (choose a name)
- Directory: ./
- Override settings: No

5. Set up environment variables in Vercel:
   - Go to your project settings in Vercel dashboard
   - Add the following environment variable:
     - `ANTHROPIC_API_KEY`: Your Claude API key

## Local Development

1. Clone the repository

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

5. Run the application:
```bash
python app.py
```

The application will be available at http://localhost:5000

## Usage

1. Upload a financial PDF document
2. View the automated analysis including:
   - Key financial metrics
   - Health assessment
   - Risk factors
   - Recommendations
   - Credit score
3. Use the chat interface to ask specific questions about the document

## Technology Stack

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- AI: Claude API (Anthropic)
- Charts: Chart.js
- Deployment: Vercel

## Troubleshooting Deployment

If you encounter permission issues:
1. Make sure you're using sudo for global npm installations:
```bash
sudo npm i -g vercel
```

2. If you still have issues, you can:
   - Install vercel locally in the project:
   ```bash
   npm init -y
   npm install vercel
   npx vercel
   ```
   
   - Or use npm with the --prefix flag:
   ```bash
   npm i -g vercel --prefix ~/.local
   ```
   Then add ~/.local/bin to your PATH:
   ```bash
   export PATH=~/.local/bin:$PATH
   ```

## Notes

- The application uses in-memory storage for document text. In a production environment, consider using a proper database.
- API keys should be kept secure and never committed to version control.
- The credit score is based on available financial metrics and should be used as one of many factors in decision-making.
