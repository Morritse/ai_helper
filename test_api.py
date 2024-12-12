import requests
import json
from pathlib import Path

def test_file_upload(file_path):
    print(f"\nTesting file: {file_path}")
    
    # Open and send the file
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f)}
        response = requests.post('http://localhost:5000/analyze', files=files)
    
    # Print results
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("\nAnalysis:")
        print(json.dumps(json.loads(result['analysis']), indent=2))
        
        # Test asking a question about the document
        doc_id = result['documentId']
        question = "What are the key financial metrics?"
        
        print(f"\nAsking question: {question}")
        response = requests.post('http://localhost:5000/ask', 
                               json={'question': question, 'documentId': doc_id})
        
        if response.status_code == 200:
            print("\nAnswer:")
            print(response.json()['answer'])
        else:
            print(f"Error asking question: {response.text}")
    else:
        print(f"Error: {response.text}")

def main():
    # Test each file type
    test_files = [
        'test_files/sample.txt',
        'test_files/financial_data.csv',
        'test_files/financial_report.docx'
    ]
    
    for file_path in test_files:
        test_file_upload(file_path)
        print("\n" + "="*50)

if __name__ == '__main__':
    main()
