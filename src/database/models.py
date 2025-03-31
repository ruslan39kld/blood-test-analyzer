from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BloodTest(db.Model):
    """Model for blood test records"""
    __tablename__ = 'blood_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    study_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Patient information
    patient_surname = db.Column(db.String(100), nullable=True, index=True)
    patient_name = db.Column(db.String(100), nullable=True)
    patient_patronymic = db.Column(db.String(100), nullable=True)
    patient_dob = db.Column(db.Date, nullable=True)
    patient_number = db.Column(db.String(50), nullable=True, index=True)  # Medical record number
    
    biomarkers = db.relationship('Biomarker', backref='blood_test', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BloodTest {self.id}: {self.patient_surname or "Unknown"} - {self.study_date}>'

    def get_full_name(self):
        """Return the patient's full name"""
        parts = []
        if self.patient_surname:
            parts.append(self.patient_surname)
        if self.patient_name:
            parts.append(self.patient_name)
        if self.patient_patronymic:
            parts.append(self.patient_patronymic)
        
        return " ".join(parts) if parts else "Unknown"


class Biomarker(db.Model):
    """Model for biomarker records"""
    __tablename__ = 'biomarkers'
    
    id = db.Column(db.Integer, primary_key=True)
    blood_test_id = db.Column(db.Integer, db.ForeignKey('blood_tests.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=True)
    reference_range_min = db.Column(db.Float, nullable=True)
    reference_range_max = db.Column(db.Float, nullable=True)
    is_abnormal = db.Column(db.Boolean, nullable=True)
    
    def __repr__(self):
        return f'<Biomarker {self.name}: {self.value} {self.unit}>'
    
    def calculate_abnormal(self):
        """Determine if the biomarker value is outside the reference range"""
        if self.reference_range_min is not None and self.reference_range_max is not None:
            return self.value < self.reference_range_min or self.value > self.reference_range_max
        return None
