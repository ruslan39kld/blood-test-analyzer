import unittest
import os
import cv2
import numpy as np
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.ocr_engine import extract_text, extract_text_with_layout, extract_tables

class TestOCREngine(unittest.TestCase):
    """Tests for the OCR engine module"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test image directory if it doesn't exist
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_images')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create a simple test image with text
        self.test_image_path = os.path.join(self.test_dir, 'test_ocr_image.png')
        self.create_test_image()
    
    def create_test_image(self):
        """Create a test image with some text for OCR testing"""
        # Create a white image
        img = np.ones((500, 800, 3), np.uint8) * 255
        
        # Add some text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, 'Blood Test Results', (50, 50), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'Date: 15.03.2025', (50, 100), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'Total Cholesterol: 5.2 mmol/L', (50, 150), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'LDL-C: 3.1 mmol/L', (50, 200), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'HDL-C: 1.5 mmol/L', (50, 250), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'Triglycerides: 1.8 mmol/L', (50, 300), font, 1, (0, 0, 0), 2)
        
        # Add a table-like structure
        cv2.rectangle(img, (50, 350), (750, 450), (0, 0, 0), 2)
        cv2.line(img, (50, 380), (750, 380), (0, 0, 0), 2)
        cv2.line(img, (400, 350), (400, 450), (0, 0, 0), 2)
        
        # Add text in the table
        cv2.putText(img, 'Parameter', (100, 370), font, 0.7, (0, 0, 0), 2)
        cv2.putText(img, 'Value', (500, 370), font, 0.7, (0, 0, 0), 2)
        cv2.putText(img, 'Glucose', (100, 420), font, 0.7, (0, 0, 0), 2)
        cv2.putText(img, '5.5 mmol/L', (500, 420), font, 0.7, (0, 0, 0), 2)
        
        # Save the image
        cv2.imwrite(self.test_image_path, img)
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test image if it exists
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
    
    def test_extract_text(self):
        """Test text extraction from image"""
        # Skip test if pytesseract is not available
        try:
            import pytesseract
        except ImportError:
            self.skipTest("Pytesseract not available")
        
        # Read the test image
        image = cv2.imread(self.test_image_path, cv2.IMREAD_GRAYSCALE)
        
        # Extract text
        try:
            text = extract_text(image)
            
            # Check that the result is a string
            self.assertIsInstance(text, str)
            
            # Check that some expected text is in the result
            # Note: OCR results may vary, so we use lower() and check for substrings
            text_lower = text.lower()
            self.assertIn('blood', text_lower)
            self.assertIn('test', text_lower)
            self.assertIn('cholesterol', text_lower)
        except Exception as e:
            # If Tesseract is not properly installed, the test will be skipped
            if "TesseractNotFoundError" in str(e):
                self.skipTest("Tesseract executable not found")
            else:
                raise
    
    def test_extract_text_with_layout(self):
        """Test text extraction with layout information"""
        # Skip test if pytesseract is not available
        try:
            import pytesseract
        except ImportError:
            self.skipTest("Pytesseract not available")
        
        # Read the test image
        image = cv2.imread(self.test_image_path, cv2.IMREAD_GRAYSCALE)
        
        # Extract text with layout
        try:
            layout_data = extract_text_with_layout(image)
            
            # Check that the result is a list
            self.assertIsInstance(layout_data, list)
            
            # Check that the list contains dictionaries
            if layout_data:
                self.assertIsInstance(layout_data[0], dict)
                
                # Check that the dictionaries have the expected keys
                expected_keys = ['text', 'x', 'y', 'width', 'height', 'conf', 'line_num', 'block_num']
                for key in expected_keys:
                    self.assertIn(key, layout_data[0])
        except Exception as e:
            # If Tesseract is not properly installed, the test will be skipped
            if "TesseractNotFoundError" in str(e):
                self.skipTest("Tesseract executable not found")
            else:
                raise
    
    def test_extract_tables(self):
        """Test table extraction from image"""
        # Skip test if pytesseract is not available
        try:
            import pytesseract
        except ImportError:
            self.skipTest("Pytesseract not available")
        
        # Read the test image
        image = cv2.imread(self.test_image_path, cv2.IMREAD_GRAYSCALE)
        
        # Extract tables
        try:
            tables = extract_tables(image)
            
            # Check that the result is a list
            self.assertIsInstance(tables, list)
            
            # Check that the list contains strings
            if tables:
                self.assertIsInstance(tables[0], str)
                
                # Check that some expected text is in the result
                # Note: OCR results may vary, so we use lower() and check for substrings
                tables_text = ' '.join(tables).lower()
                self.assertIn('parameter', tables_text)
                self.assertIn('value', tables_text)
                self.assertIn('glucose', tables_text)
        except Exception as e:
            # If Tesseract is not properly installed, the test will be skipped
            if "TesseractNotFoundError" in str(e):
                self.skipTest("Tesseract executable not found")
            else:
                raise

if __name__ == '__main__':
    unittest.main()
