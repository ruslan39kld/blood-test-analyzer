import os
import sqlite3
import logging
import sys
import subprocess
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix the database schema by recreating the database with correct columns."""
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blood_test.db')
        
        # Check if the database file exists and remove it
        if os.path.exists(db_path):
            logger.info(f"Removing existing database at {db_path}")
            os.remove(db_path)
            logger.info("Existing database removed successfully")
        
        # Run the init_db.py script to recreate the database
        logger.info("Running init_db.py to recreate the database...")
        subprocess.run([sys.executable, "init_db.py"], check=True)
        logger.info("Database recreated successfully")
        
        # Verify the schema
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
            return False
        else:
            logger.info("All required columns are present in the blood_tests table")
            return True
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {str(e)}")
        return False

def fix_date_patterns_import():
    """Fix the DATE_PATTERNS import issue in ocr_engine.py."""
    try:
        ocr_engine_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      'src', 'processing', 'ocr_engine.py')
        
        # Read the current content
        with open(ocr_engine_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the import is already there
        if 'from src.processing.nlp_analyzer import DATE_PATTERNS' in content:
            logger.info("DATE_PATTERNS import already exists in ocr_engine.py")
            return True
        
        # Add the import if it's not there
        import_line = 'from src.processing.nlp_analyzer import DATE_PATTERNS'
        lines = content.split('\n')
        
        # Find a good place to add the import (after other imports)
        import_section_end = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_section_end = i + 1
        
        # Insert the import line
        lines.insert(import_section_end, import_line)
        
        # Write the modified content back
        with open(ocr_engine_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info("Added DATE_PATTERNS import to ocr_engine.py")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing DATE_PATTERNS import: {str(e)}")
        return False

def restart_application():
    """Restart the Flask application."""
    try:
        # Find any running Flask processes
        logger.info("Attempting to restart the Flask application...")
        
        # On Windows, we'll just provide instructions
        logger.info("To restart the application, please run the following command:")
        logger.info("python app.py")
        
        return True
    except Exception as e:
        logger.error(f"Error restarting application: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting comprehensive fix for Blood Test Analyzer...")
    
    # Fix database schema
    db_fixed = fix_database_schema()
    if db_fixed:
        logger.info("Database schema fixed successfully")
    else:
        logger.error("Failed to fix database schema")
    
    # Fix DATE_PATTERNS import
    date_patterns_fixed = fix_date_patterns_import()
    if date_patterns_fixed:
        logger.info("DATE_PATTERNS import fixed successfully")
    else:
        logger.error("Failed to fix DATE_PATTERNS import")
    
    # Restart application
    restart_application()
    
    if db_fixed and date_patterns_fixed:
        logger.info("All issues fixed successfully! Please restart the application manually.")
    else:
        logger.error("Some issues could not be fixed. Please check the logs for details.")
