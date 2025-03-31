import unittest
import sys
import os
from pathlib import Path
from datetime import datetime, date
import tempfile

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from src.database.models import db, BloodTest, Biomarker
from src.database.operations import save_blood_test, get_blood_test, get_all_blood_tests, search_blood_tests, delete_blood_test

class TestDatabase(unittest.TestCase):
    """Tests for the database models and operations"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        # Use an in-memory SQLite database for testing
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize the database
        db.init_app(self.app)
        
        # Create the application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create the database tables
        db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        # Drop the database tables
        db.session.remove()
        db.drop_all()
        
        # Pop the application context
        self.app_context.pop()
    
    def test_blood_test_model(self):
        """Test BloodTest model"""
        # Create a BloodTest instance
        blood_test = BloodTest(
            filename='test.jpg',
            study_date=date(2025, 3, 15)
        )
        
        # Add to the database
        db.session.add(blood_test)
        db.session.commit()
        
        # Query the database
        saved_test = BloodTest.query.first()
        
        # Check that the instance was saved correctly
        self.assertEqual(saved_test.filename, 'test.jpg')
        self.assertEqual(saved_test.study_date, date(2025, 3, 15))
        self.assertIsNotNone(saved_test.created_at)
    
    def test_biomarker_model(self):
        """Test Biomarker model"""
        # Create a BloodTest instance
        blood_test = BloodTest(
            filename='test.jpg',
            study_date=date(2025, 3, 15)
        )
        
        # Add to the database
        db.session.add(blood_test)
        db.session.flush()
        
        # Create a Biomarker instance
        biomarker = Biomarker(
            blood_test_id=blood_test.id,
            name='total_cholesterol',
            value=5.2,
            unit='mmol/l',
            reference_range_min=3.5,
            reference_range_max=5.5
        )
        
        # Add to the database
        db.session.add(biomarker)
        db.session.commit()
        
        # Query the database
        saved_biomarker = Biomarker.query.first()
        
        # Check that the instance was saved correctly
        self.assertEqual(saved_biomarker.name, 'total_cholesterol')
        self.assertEqual(saved_biomarker.value, 5.2)
        self.assertEqual(saved_biomarker.unit, 'mmol/l')
        self.assertEqual(saved_biomarker.reference_range_min, 3.5)
        self.assertEqual(saved_biomarker.reference_range_max, 5.5)
        
        # Check the relationship
        self.assertEqual(saved_biomarker.blood_test.filename, 'test.jpg')
    
    def test_save_blood_test(self):
        """Test save_blood_test function"""
        # Create biomarkers data
        biomarkers_data = {
            'total_cholesterol': {
                'value': 5.2,
                'unit': 'mmol/l',
                'reference_range_min': 3.5,
                'reference_range_max': 5.5
            },
            'ldl_c': {
                'value': 3.1,
                'unit': 'mmol/l'
            },
            'hdl_c': {
                'value': 1.5,
                'unit': 'mmol/l'
            }
        }
        
        # Save to the database
        study_date = date(2025, 3, 15)
        filename = 'test.jpg'
        test_id = save_blood_test(biomarkers_data, study_date, filename)
        
        # Check that the function returned an ID
        self.assertIsNotNone(test_id)
        
        # Query the database
        blood_test = BloodTest.query.get(test_id)
        biomarkers = Biomarker.query.filter_by(blood_test_id=test_id).all()
        
        # Check that the blood test was saved correctly
        self.assertEqual(blood_test.filename, filename)
        self.assertEqual(blood_test.study_date, study_date)
        
        # Check that the biomarkers were saved correctly
        self.assertEqual(len(biomarkers), 3)
        
        # Check specific biomarker
        cholesterol = next((b for b in biomarkers if b.name == 'total_cholesterol'), None)
        self.assertIsNotNone(cholesterol)
        self.assertEqual(cholesterol.value, 5.2)
        self.assertEqual(cholesterol.unit, 'mmol/l')
        self.assertEqual(cholesterol.reference_range_min, 3.5)
        self.assertEqual(cholesterol.reference_range_max, 5.5)
    
    def test_get_blood_test(self):
        """Test get_blood_test function"""
        # Create a blood test with biomarkers
        blood_test = BloodTest(
            filename='test.jpg',
            study_date=date(2025, 3, 15)
        )
        db.session.add(blood_test)
        db.session.flush()
        
        biomarker = Biomarker(
            blood_test_id=blood_test.id,
            name='total_cholesterol',
            value=5.2,
            unit='mmol/l'
        )
        db.session.add(biomarker)
        db.session.commit()
        
        # Get the blood test
        retrieved_test, retrieved_biomarkers = get_blood_test(blood_test.id)
        
        # Check that the blood test was retrieved correctly
        self.assertEqual(retrieved_test.id, blood_test.id)
        self.assertEqual(retrieved_test.filename, 'test.jpg')
        
        # Check that the biomarkers were retrieved correctly
        self.assertEqual(len(retrieved_biomarkers), 1)
        self.assertEqual(retrieved_biomarkers[0].name, 'total_cholesterol')
    
    def test_delete_blood_test(self):
        """Test delete_blood_test function"""
        # Create a blood test with biomarkers
        blood_test = BloodTest(
            filename='test.jpg',
            study_date=date(2025, 3, 15)
        )
        db.session.add(blood_test)
        db.session.flush()
        
        biomarker = Biomarker(
            blood_test_id=blood_test.id,
            name='total_cholesterol',
            value=5.2,
            unit='mmol/l'
        )
        db.session.add(biomarker)
        db.session.commit()
        
        # Delete the blood test
        result = delete_blood_test(blood_test.id)
        
        # Check that the function returned True
        self.assertTrue(result)
        
        # Check that the blood test was deleted
        self.assertIsNone(BloodTest.query.get(blood_test.id))
        
        # Check that the biomarkers were deleted
        biomarkers = Biomarker.query.filter_by(blood_test_id=blood_test.id).all()
        self.assertEqual(len(biomarkers), 0)

if __name__ == '__main__':
    unittest.main()
