import unittest
import os
import cv2
import numpy as np
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.image_processor import preprocess_image, detect_table_areas, extract_roi

class TestImageProcessor(unittest.TestCase):
    """Tests for the image processing module"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test image directory if it doesn't exist
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_images')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create a simple test image
        self.test_image_path = os.path.join(self.test_dir, 'test_image.png')
        self.create_test_image()
    
    def create_test_image(self):
        """Create a test image with some text"""
        # Create a white image
        img = np.ones((500, 800, 3), np.uint8) * 255
        
        # Add some text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, 'Total Cholesterol: 5.2 mmol/L', (50, 50), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'LDL-C: 3.1 mmol/L', (50, 100), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'HDL-C: 1.5 mmol/L', (50, 150), font, 1, (0, 0, 0), 2)
        cv2.putText(img, 'Triglycerides: 1.8 mmol/L', (50, 200), font, 1, (0, 0, 0), 2)
        
        # Add a table-like structure
        cv2.rectangle(img, (50, 250), (750, 400), (0, 0, 0), 2)
        cv2.line(img, (50, 300), (750, 300), (0, 0, 0), 2)
        cv2.line(img, (400, 250), (400, 400), (0, 0, 0), 2)
        
        # Save the image
        cv2.imwrite(self.test_image_path, img)
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test image if it exists
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        
        # Remove preprocessed image if it exists
        preprocessed_path = os.path.join(self.test_dir, 'preprocessed_test_image.png')
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)
    
    def test_preprocess_image(self):
        """Test image preprocessing"""
        # Skip test if OpenCV is not available
        try:
            import cv2
        except ImportError:
            self.skipTest("OpenCV not available")
        
        # Preprocess the test image
        preprocessed = preprocess_image(self.test_image_path)
        
        # Check that the result is a numpy array
        self.assertIsInstance(preprocessed, np.ndarray)
        
        # Check that the image is grayscale
        self.assertEqual(len(preprocessed.shape), 2)
        
        # Check that the preprocessed image exists
        preprocessed_path = os.path.join(self.test_dir, 'preprocessed_test_image.png')
        self.assertTrue(os.path.exists(preprocessed_path))
    
    def test_detect_table_areas(self):
        """Test table area detection"""
        # Skip test if OpenCV is not available
        try:
            import cv2
        except ImportError:
            self.skipTest("OpenCV not available")
        
        # Read the test image
        image = cv2.imread(self.test_image_path, cv2.IMREAD_GRAYSCALE)
        
        # Detect table areas
        table_rects = detect_table_areas(image)
        
        # Check that at least one table was detected
        self.assertGreaterEqual(len(table_rects), 1)
        
        # Check that the detected rectangles have the correct format
        for rect in table_rects:
            self.assertEqual(len(rect), 4)  # x, y, width, height
    
    def test_extract_roi(self):
        """Test region of interest extraction"""
        # Skip test if OpenCV is not available
        try:
            import cv2
        except ImportError:
            self.skipTest("OpenCV not available")
        
        # Read the test image
        image = cv2.imread(self.test_image_path)
        
        # Extract header ROI
        header_roi = extract_roi(image, 'header')
        
        # Check that the ROI is a numpy array
        self.assertIsInstance(header_roi, np.ndarray)
        
        # Check that the ROI has the correct shape
        self.assertEqual(header_roi.shape[0], int(image.shape[0] * 0.2))
        self.assertEqual(header_roi.shape[1], image.shape[1])
        
        # Extract table ROI
        table_roi = extract_roi(image, 'table')
        
        # Check that the ROI is a numpy array
        self.assertIsInstance(table_roi, np.ndarray)
        
        # Check that the ROI has the correct shape
        self.assertEqual(table_roi.shape[0], int(image.shape[0] * 0.6))
        self.assertEqual(table_roi.shape[1], image.shape[1])

if __name__ == '__main__':
    unittest.main()
