from datetime import datetime
from .models import db, BloodTest, Biomarker
import logging

logger = logging.getLogger(__name__)

def save_blood_test(biomarkers_data, study_date, filename, patient_info=None):
    """
    Save blood test results to the database
    
    Args:
        biomarkers_data (dict): Dictionary of biomarkers with name, value, and unit
        study_date (datetime.date): Date of the study
        filename (str): Original filename
        patient_info (dict): Dictionary with patient information
        
    Returns:
        int: ID of the created blood test record
    """
    try:
        # Create new blood test record
        blood_test = BloodTest(
            filename=filename,
            study_date=study_date
        )
        
        # Add patient information if available
        if patient_info:
            blood_test.patient_surname = patient_info.get('patient_surname')
            blood_test.patient_name = patient_info.get('patient_name')
            blood_test.patient_patronymic = patient_info.get('patient_patronymic')
            blood_test.patient_dob = patient_info.get('patient_dob')
            blood_test.patient_number = patient_info.get('patient_number')
        
        db.session.add(blood_test)
        db.session.flush()  # Get the ID without committing
        
        # Add biomarkers
        for biomarker_name, biomarker_info in biomarkers_data.items():
            reference_range = biomarker_info.get('reference_range', {})
            
            biomarker = Biomarker(
                blood_test_id=blood_test.id,
                name=biomarker_name,
                value=biomarker_info['value'],
                unit=biomarker_info.get('unit'),
                reference_range_min=reference_range.get('min'),
                reference_range_max=reference_range.get('max'),
                is_abnormal=biomarker_info.get('is_abnormal')
            )
            db.session.add(biomarker)
        
        # Commit the transaction
        db.session.commit()
        logger.info(f"Saved blood test with ID {blood_test.id} and {len(biomarkers_data)} biomarkers")
        return blood_test.id
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving blood test: {str(e)}")
        raise

def get_blood_test(test_id):
    """
    Get blood test by ID
    
    Args:
        test_id (int): Blood test ID
        
    Returns:
        tuple: (BloodTest, list of Biomarker)
    """
    blood_test = BloodTest.query.get(test_id)
    if not blood_test:
        return None, []
    
    biomarkers = Biomarker.query.filter_by(blood_test_id=test_id).all()
    return blood_test, biomarkers

def get_all_blood_tests(page=1, per_page=10, sort_by='study_date', sort_order='desc'):
    """
    Get all blood tests with pagination
    
    Args:
        page (int): Page number
        per_page (int): Items per page
        sort_by (str): Field to sort by (study_date, patient_surname, patient_number, created_at)
        sort_order (str): Sort order (asc or desc)
        
    Returns:
        Pagination object
    """
    try:
        query = BloodTest.query
        
        # Apply sorting
        if sort_by == 'study_date':
            order_field = BloodTest.study_date
        elif sort_by == 'patient_surname':
            order_field = BloodTest.patient_surname
        elif sort_by == 'patient_number':
            order_field = BloodTest.patient_number
        elif sort_by == 'created_at':
            order_field = BloodTest.created_at
        else:
            order_field = BloodTest.study_date
        
        if sort_order == 'asc':
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
        
        return query.paginate(page=page, per_page=per_page)
    except Exception as e:
        logger.error(f"Error retrieving blood tests: {str(e)}")
        # Return empty pagination object
        return BloodTest.query.filter(BloodTest.id < 0).paginate(page=page, per_page=per_page)

def search_blood_tests(start_date=None, end_date=None, biomarker_name=None, patient_surname=None, patient_number=None):
    """
    Search blood tests by date range, biomarker name, patient surname, or patient number
    
    Args:
        start_date (datetime.date): Start date for search
        end_date (datetime.date): End date for search
        biomarker_name (str): Name of biomarker to search for
        patient_surname (str): Patient surname to search for
        patient_number (str): Patient number to search for
        
    Returns:
        list: List of BloodTest objects
    """
    query = BloodTest.query
    
    # Apply date filters
    if start_date:
        query = query.filter(BloodTest.study_date >= start_date)
    if end_date:
        query = query.filter(BloodTest.study_date <= end_date)
    
    # Apply patient filters
    if patient_surname:
        query = query.filter(BloodTest.patient_surname.ilike(f'%{patient_surname}%'))
    if patient_number:
        query = query.filter(BloodTest.patient_number == patient_number)
    
    # Apply biomarker filter
    if biomarker_name:
        query = query.join(Biomarker).filter(Biomarker.name == biomarker_name)
    
    return query.order_by(BloodTest.study_date.desc()).all()

def get_biomarker_history(biomarker_name, patient_surname=None, patient_number=None):
    """
    Get history of a specific biomarker for a patient
    
    Args:
        biomarker_name (str): Name of the biomarker
        patient_surname (str): Patient surname
        patient_number (str): Patient number
        
    Returns:
        list: List of (date, value, unit) tuples for the biomarker
    """
    query = db.session.query(
        BloodTest.study_date,
        Biomarker.value,
        Biomarker.unit,
        Biomarker.is_abnormal
    ).join(
        Biomarker, BloodTest.id == Biomarker.blood_test_id
    ).filter(
        Biomarker.name == biomarker_name
    )
    
    if patient_surname:
        query = query.filter(BloodTest.patient_surname.ilike(f'%{patient_surname}%'))
    if patient_number:
        query = query.filter(BloodTest.patient_number == patient_number)
    
    results = query.order_by(BloodTest.study_date).all()
    return [(r[0], r[1], r[2], r[3]) for r in results]

def delete_blood_test(test_id):
    """
    Delete blood test by ID
    
    Args:
        test_id (int): Blood test ID
        
    Returns:
        bool: Success status
    """
    try:
        blood_test = BloodTest.query.get(test_id)
        if not blood_test:
            return False
        
        db.session.delete(blood_test)
        db.session.commit()
        logger.info(f"Deleted blood test with ID {test_id}")
        return True
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting blood test: {str(e)}")
        return False
