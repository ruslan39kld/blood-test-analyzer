import os
import sqlite3
import logging
from src.database.models import db, BloodTest, Biomarker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blood_test.db')

def recreate_database():
    """Completely recreate the database with the correct schema."""
    try:
        # Check if the database file exists and remove it
        if os.path.exists(db_path):
            logger.info(f"Removing existing database at {db_path}")
            os.remove(db_path)
            logger.info("Existing database removed successfully")
        
        # Import and initialize the Flask app to create the database
        from src.app import app
        
        # Use the app context to create the database
        with app.app_context():
            logger.info("Creating new database with SQLAlchemy")
            db.create_all()
            logger.info("Database created successfully")
        
        # Verify the schema using SQLite directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check the blood_tests table schema
        cursor.execute("PRAGMA table_info(blood_tests)")
        columns = cursor.fetchall()
        logger.info("Blood tests table schema:")
        column_names = [column[1] for column in columns]
        for column in columns:
            logger.info(f"  {column[1]} ({column[2]})")
        
        # Verify that all required columns are present
        required_columns = [
            "id", "filename", "study_date", "created_at",
            "patient_surname", "patient_name", "patient_patronymic", 
            "patient_dob", "patient_number"
        ]
        
        missing_columns = [col for col in required_columns if col not in column_names]
        if missing_columns:
            logger.error(f"Missing columns in blood_tests table: {missing_columns}")
            raise ValueError(f"Database schema is still missing columns: {missing_columns}")
        else:
            logger.info("All required columns are present in the blood_tests table")
        
        # Check the biomarker table schema
        cursor.execute("PRAGMA table_info(biomarker)")
        columns = cursor.fetchall()
        logger.info("Biomarker table schema:")
        for column in columns:
            logger.info(f"  {column[1]} ({column[2]})")
        
        conn.close()
        logger.info("Database schema verification completed successfully")
        
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting database recreation process")
    recreate_database()
    logger.info("Database recreation process completed")
