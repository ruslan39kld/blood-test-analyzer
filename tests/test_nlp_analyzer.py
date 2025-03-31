import unittest
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.nlp_analyzer import extract_biomarkers, extract_date, extract_unit, extract_reference_range

class TestNLPAnalyzer(unittest.TestCase):
    """Tests for the NLP analyzer module"""
    
    def test_extract_biomarkers(self):
        """Test biomarker extraction from text"""
        # Sample text with biomarker information
        text = """
        Blood Test Results
        Date: 15.03.2025
        
        Total Cholesterol: 5.2 mmol/L (ref: 3.5-5.5)
        LDL-C: 3.1 mmol/L
        HDL-C: 1.5 mmol/L
        Triglycerides: 1.8 mmol/L
        Glucose: 5.5 mmol/L
        Creatinine: 80 umol/L
        ALT: 25 U/L
        AST: 22 U/L
        """
        
        # Extract biomarkers
        biomarkers, study_date = extract_biomarkers(text)
        
        # Check that biomarkers were extracted
        self.assertIsInstance(biomarkers, dict)
        
        # Check that expected biomarkers are present
        expected_biomarkers = ['total_cholesterol', 'ldl_c', 'hdl_c', 'triglycerides', 'glucose', 'creatinine', 'alt', 'ast']
        for biomarker in expected_biomarkers:
            self.assertIn(biomarker, biomarkers)
        
        # Check specific biomarker values
        self.assertEqual(biomarkers['total_cholesterol']['value'], 5.2)
        self.assertEqual(biomarkers['total_cholesterol']['unit'], 'mmol/l')
        
        # Check study date
        self.assertIsInstance(study_date, datetime.date)
        self.assertEqual(study_date.day, 15)
        self.assertEqual(study_date.month, 3)
        self.assertEqual(study_date.year, 2025)
    
    def test_extract_date(self):
        """Test date extraction from text"""
        # Test various date formats
        date_texts = [
            "Date: 15.03.2025",
            "Date: 15/03/2025",
            "Date: 15-03-2025",
            "Date: 2025.03.15",
            "Date: 2025/03/15",
            "Date: 2025-03-15",
            "Sample collected on 15.03.2025",
            "15.03.2025"
        ]
        
        for text in date_texts:
            date = extract_date(text)
            self.assertIsInstance(date, datetime.date)
            self.assertEqual(date.day, 15)
            self.assertEqual(date.month, 3)
            self.assertEqual(date.year, 2025)
    
    def test_extract_unit(self):
        """Test unit extraction from text"""
        # Test various unit formats
        unit_texts = [
            "5.2 mmol/L",
            "5.2 ммоль/л",
            "80 umol/L",
            "80 мкмоль/л",
            "25 U/L",
            "25 ед/л",
            "25 IU/L",
            "14 g/L",
            "14 г/л",
            "5.5%"
        ]
        
        expected_units = [
            "mmol/l",
            "mmol/l",
            "umol/l",
            "umol/l",
            "u/l",
            "u/l",
            "u/l",
            "g/l",
            "g/l",
            "%"
        ]
        
        for text, expected_unit in zip(unit_texts, expected_units):
            unit = extract_unit(text)
            self.assertEqual(unit, expected_unit)
    
    def test_extract_reference_range(self):
        """Test reference range extraction from text"""
        # Test various reference range formats
        range_texts = [
            "5.2 mmol/L (ref: 3.5-5.5)",
            "5.2 mmol/L (reference: 3.5-5.5)",
            "5.2 mmol/L (norm: 3.5-5.5)",
            "5.2 mmol/L (3.5-5.5)",
            "5.2 mmol/L [3.5-5.5]",
            "5.2 mmol/L {3.5-5.5}",
            "5.2 mmol/L норма: 3.5-5.5",
            "5.2 mmol/L референс: 3.5-5.5"
        ]
        
        for text in range_texts:
            range_dict = extract_reference_range(text)
            self.assertIsInstance(range_dict, dict)
            self.assertIn('reference_range_min', range_dict)
            self.assertIn('reference_range_max', range_dict)
            self.assertEqual(range_dict['reference_range_min'], 3.5)
            self.assertEqual(range_dict['reference_range_max'], 5.5)

if __name__ == '__main__':
    unittest.main()
