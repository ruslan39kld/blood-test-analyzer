import unittest
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app
from src.database.models import db, BloodTest, Biomarker

class TestApp(unittest.TestCase):
    """Tests for the Flask application"""
    
    def setUp(self):
        """Set up test environment"""
        # Configure Flask for testing
        flask_app.config['TESTING'] = True
        flask_app.config['WTF_CSRF_ENABLED'] = False
        
        # Use an in-memory SQLite database for testing
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        # Create a temporary directory for uploads
        self.temp_dir = tempfile.mkdtemp()
        flask_app.config['UPLOAD_FOLDER'] = self.temp_dir
        
        # Create the test client
        self.client = flask_app.test_client()
        
        # Create the application context
        self.app_context = flask_app.app_context()
        self.app_context.push()
        
        # Create the database tables
        db.create_all()
        
        # Create a sample blood test for testing
        blood_test = BloodTest(
            filename='sample.jpg',
            study_date='2025-03-15'
        )
        db.session.add(blood_test)
        db.session.flush()
        
        # Add some biomarkers
        biomarkers = [
            Biomarker(blood_test_id=blood_test.id, name='total_cholesterol', value=5.2, unit='mmol/l'),
            Biomarker(blood_test_id=blood_test.id, name='ldl_c', value=3.1, unit='mmol/l'),
            Biomarker(blood_test_id=blood_test.id, name='hdl_c', value=1.5, unit='mmol/l')
        ]
        db.session.add_all(biomarkers)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        # Drop the database tables
        db.session.remove()
        db.drop_all()
        
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
        
        # Pop the application context
        self.app_context.pop()
    
    def test_index_route(self):
        """Test the index route"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload Blood Test Document', response.data)
    
    def test_results_route(self):
        """Test the results route"""
        response = self.client.get('/results')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Blood Test Results', response.data)
        self.assertIn(b'sample.jpg', response.data)
    
    def test_view_result_route(self):
        """Test the view_result route"""
        # Get the ID of the sample blood test
        blood_test = BloodTest.query.first()
        
        response = self.client.get(f'/result/{blood_test.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Information', response.data)
        self.assertIn(b'total_cholesterol', response.data.lower())
        self.assertIn(b'5.2', response.data)
    
    def test_api_get_blood_tests(self):
        """Test the API endpoint for getting all blood tests"""
        response = self.client.get('/api/blood-tests')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Check that the response contains the expected data
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['filename'], 'sample.jpg')
        self.assertEqual(len(data[0]['biomarkers']), 3)
    
    def test_api_get_blood_test(self):
        """Test the API endpoint for getting a specific blood test"""
        # Get the ID of the sample blood test
        blood_test = BloodTest.query.first()
        
        response = self.client.get(f'/api/blood-test/{blood_test.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Check that the response contains the expected data
        data = response.get_json()
        self.assertEqual(data['id'], blood_test.id)
        self.assertEqual(data['filename'], 'sample.jpg')
        self.assertEqual(len(data['biomarkers']), 3)
    
    def test_404_error(self):
        """Test the 404 error handler"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Page Not Found', response.data)

if __name__ == '__main__':
    unittest.main()
