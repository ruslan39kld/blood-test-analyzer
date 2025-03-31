import os
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blood_test.db')

def fix_database_schema():
    """Fix the database schema by adding missing patient columns."""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the blood_tests table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blood_tests'")
        if not cursor.fetchone():
            logger.info("Creating blood_tests table from scratch...")
            # Create the table with all required columns
            cursor.execute('''
                CREATE TABLE blood_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    study_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    patient_surname TEXT,
                    patient_name TEXT,
                    patient_patronymic TEXT,
                    patient_dob DATE,
                    patient_number TEXT
                )
            ''')
            logger.info("Created blood_tests table with all required columns")
        else:
            # Check if the patient columns exist
            logger.info("Checking for missing columns in blood_tests table...")
            
            # Get existing columns
            cursor.execute("PRAGMA table_info(blood_tests)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            # Define required patient columns
            patient_columns = [
                "patient_surname", 
                "patient_name", 
                "patient_patronymic", 
                "patient_dob", 
                "patient_number"
            ]
            
            # Add missing columns
            for column in patient_columns:
                if column not in existing_columns:
                    logger.info(f"Adding missing column: {column}")
                    cursor.execute(f"ALTER TABLE blood_tests ADD COLUMN {column} TEXT")
            
        # Check if the biomarkers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='biomarker'")
        if not cursor.fetchone():
            logger.info("Creating biomarker table...")
            # Create the biomarkers table
            cursor.execute('''
                CREATE TABLE biomarker (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    blood_test_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    reference_range_min REAL,
                    reference_range_max REAL,
                    is_abnormal BOOLEAN,
                    FOREIGN KEY (blood_test_id) REFERENCES blood_tests (id) ON DELETE CASCADE
                )
            ''')
            logger.info("Created biomarker table")
        
        # Commit the changes
        conn.commit()
        logger.info("Database schema fixed successfully!")
        
        # Verify the schema
        cursor.execute("PRAGMA table_info(blood_tests)")
        columns = cursor.fetchall()
        logger.info("Current blood_tests table schema:")
        for column in columns:
            logger.info(f"  {column[1]} ({column[2]})")
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {str(e)}")
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    # Check if the database exists
    if os.path.exists(db_path):
        logger.info(f"Found existing database at {db_path}")
    else:
        logger.info(f"Database not found at {db_path}, will create a new one")
    
    # Fix the schema
    fix_database_schema()
