import unittest
import io
import os
import sys
from unittest.mock import patch
import pandas as pd
from docx import Document

# Mock environment variables and imports before importing app
with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'mock_key'}):
    import app

class TestFileHandlers(unittest.TestCase):
    def setUp(self):
        # Suppress logging output during tests
        app.logger.setLevel('ERROR')

    def test_txt_handler(self):
        """Test TXT file handling"""
        txt_content = b'Test text content\nwith multiple lines\nand some numbers: 123'
        text = app.extract_text_from_txt(txt_content)
        self.assertIsInstance(text, str)
        self.assertTrue('Test text content' in text)
        self.assertTrue('123' in text)

    def test_csv_handler(self):
        """Test CSV file handling"""
        csv_data = "col1,col2,col3\n1,2,3\n4,5,6"
        csv_content = csv_data.encode('utf-8')
        text = app.extract_text_from_csv(csv_content)
        self.assertIsInstance(text, str)
        self.assertTrue('col1' in text)
        self.assertTrue('Records:' in text)

    def test_docx_handler(self):
        """Test DOCX file handling"""
        doc = Document()
        doc.add_paragraph('Test DOCX content')
        doc_stream = io.BytesIO()
        doc.save(doc_stream)
        doc_content = doc_stream.getvalue()
        
        text = app.extract_text_from_docx(doc_content)
        self.assertIsInstance(text, str)
        self.assertTrue('Test DOCX content' in text)

    def test_invalid_content(self):
        """Test handling of invalid file content"""
        invalid_content = b'Invalid file content'
        
        # TXT should handle any content
        text = app.extract_text_from_txt(invalid_content)
        self.assertEqual(text.strip(), 'Invalid file content')
        
        # CSV should raise ValueError for invalid content
        with self.assertRaises(ValueError):
            app.extract_text_from_csv(invalid_content)
            
        # DOCX should raise ValueError for invalid content
        with self.assertRaises(ValueError):
            app.extract_text_from_docx(invalid_content)

if __name__ == '__main__':
    unittest.main()
