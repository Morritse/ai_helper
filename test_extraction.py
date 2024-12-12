import sys
from pathlib import Path
sys.path.append('.')

from app import (
    extract_text_from_txt,
    extract_text_from_csv,
    extract_text_from_docx
)

def test_extraction(file_path):
    print(f"\nTesting file: {file_path}")
    
    try:
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Get file extension
        ext = Path(file_path).suffix.lower()
        
        # Extract text based on file type
        if ext == '.txt':
            text = extract_text_from_txt(content)
        elif ext == '.csv':
            text = extract_text_from_csv(content)
        elif ext == '.docx':
            text = extract_text_from_docx(content)
        else:
            print(f"Unsupported file type: {ext}")
            return
            
        print("\nExtracted text preview (first 500 chars):")
        print("-" * 50)
        print(text[:500])
        print("-" * 50)
        print(f"\nTotal characters extracted: {len(text)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    # Test each file type
    test_files = [
        'test_files/sample.txt',
        'test_files/financial_data.csv',
        'test_files/financial_report.docx'
    ]
    
    for file_path in test_files:
        test_extraction(file_path)
        print("\n" + "="*50)

if __name__ == '__main__':
    main()
