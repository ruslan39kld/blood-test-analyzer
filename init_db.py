import os
import sqlite3
from app import app, db
from src.database.models import BloodTest, Biomarker

# First, ensure the SQLite database file exists
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blood_test.db')
if os.path.exists(db_path):
    os.remove(db_path)  # Remove existing database to start fresh
    print(f"Removed existing database at {db_path}")

# Create the database tables using SQLAlchemy
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
    
    # Verify tables were created
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Created tables: {tables}")
    conn.close()
