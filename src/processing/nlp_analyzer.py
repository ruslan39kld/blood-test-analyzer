import re
import spacy
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

# Load spaCy models
try:
    # Try to load Russian model
    nlp_ru = spacy.load("ru_core_news_sm")
except OSError:
    logger.warning("Russian spaCy model not found. You may need to download it with: python -m spacy download ru_core_news_sm")
    nlp_ru = None

try:
    # Try to load English model
    nlp_en = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("English spaCy model not found. You may need to download it with: python -m spacy download en_core_web_sm")
    nlp_en = None

# Define biomarker patterns
BIOMARKER_PATTERNS = {
    'total_cholesterol': [r'(?i)общий\s+холестерин', r'(?i)total\s+cholesterol', r'(?i)холестерин\s+общий'],
    'ldl_c': [r'(?i)лпнп', r'(?i)ldl[-\s]c', r'(?i)холестерин\s+лпнп', r'(?i)ldl\s+cholesterol'],
    'hdl_c': [r'(?i)лпвп', r'(?i)hdl[-\s]c', r'(?i)холестерин\s+лпвп', r'(?i)hdl\s+cholesterol'],
    'triglycerides': [r'(?i)триглицериды', r'(?i)triglycerides', r'(?i)тг', r'(?i)tg'],
    'creatinine': [r'(?i)креатинин', r'(?i)creatinine'],
    'urea': [r'(?i)мочевина', r'(?i)urea'],
    'uric_acid': [r'(?i)мочевая\s+кислота', r'(?i)uric\s+acid'],
    'alt': [r'(?i)алт', r'(?i)alt', r'(?i)аланинаминотрансфераза', r'(?i)alanine\s+aminotransferase'],
    'ast': [r'(?i)аст', r'(?i)ast', r'(?i)аспартатаминотрансфераза', r'(?i)aspartate\s+aminotransferase'],
    'crp': [r'(?i)срб', r'(?i)c-реактивный\s+белок', r'(?i)crp', r'(?i)c-reactive\s+protein'],
    'total_bilirubin': [r'(?i)общий\s+билирубин', r'(?i)билирубин\s+общий', r'(?i)total\s+bilirubin'],
    'potassium': [r'(?i)калий', r'(?i)potassium', r'(?i)k\+?'],
    'sodium': [r'(?i)натрий', r'(?i)sodium', r'(?i)na\+?'],
    'glucose': [r'(?i)глюкоза', r'(?i)glucose'],
    'glycated_hemoglobin': [r'(?i)гликированн?ый\s+гемоглобин', r'(?i)glycated\s+h[ae]moglobin', r'(?i)hba1c'],
    'ttg': [r'(?i)ттг', r'(?i)тиреотропный\s+гормон', r'(?i)tsh', r'(?i)thyroid\s+stimulating\s+hormone'],
    't4': [r'(?i)т4', r'(?i)тироксин', r'(?i)t4', r'(?i)thyroxine']
}

# Define date patterns
DATE_PATTERNS = [
    r'(\d{2})[./\\-](\d{2})[./\\-](\d{4})',            # DD/MM/YYYY
    r'(\d{2})[./\\-](\d{2})[./\\-](\d{2})',            # DD/MM/YY
    r'(\d{4})[./\\-](\d{2})[./\\-](\d{2})',            # YYYY/MM/DD
    r'(\d{1,2})\s+(?:января|янв|февраля|фев|марта|мар|апреля|апр|мая|июня|июн|июля|июл|августа|авг|сентября|сен|октября|окт|ноября|ноя|декабря|дек)\s+(\d{4})',  # DD Month YYYY (Russian)
    r'(\d{1,2})\s+(?:january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec)\s+(\d{4})',  # DD Month YYYY (English)
]

# Define unit patterns
UNIT_PATTERNS = {
    'mmol/l': [r'ммоль/л', r'mmol/l'],
    'mg/dl': [r'мг/дл', r'mg/dl'],
    'umol/l': [r'мкмоль/л', r'umol/l'],
    'g/l': [r'г/л', r'g/l'],
    'u/l': [r'ед/л', r'u/l'],
    'miu/l': [r'мМЕ/л', r'miu/l'],
    'pmol/l': [r'пмоль/л', r'pmol/l'],
    'mmol/mol': [r'ммоль/моль', r'mmol/mol'],
    '%': [r'%']
}

# Patient information patterns
PATIENT_PATTERNS = {
    'full_name': [
        r'(?i)пациент:?\s*([А-Яа-яЁё]+\s+[А-Яа-яЁё]+(?:\s+[А-Яа-яЁё]+)?)',
        r'(?i)patient:?\s*([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)',
        r'(?i)ф\.?и\.?о\.?:?\s*([А-Яа-яЁё]+\s+[А-Яа-яЁё]+(?:\s+[А-Яа-яЁё]+)?)',
        r'(?i)name:?\s*([A-Za-z]+\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)'
    ],
    'medical_number': [
        r'(?i)(?:номер|карты|карта|№):?\s*(\d+)',
        r'(?i)(?:number|card|id|#):?\s*(\d+)'
    ],
    'date_of_birth': [
        r'(?i)(?:дата\s+рождения|д\.р\.|дата\s+р-я):?\s*(\d{1,2}[.-/]\d{1,2}[.-/]\d{2,4})',
        r'(?i)(?:date\s+of\s+birth|dob|birth\s+date):?\s*(\d{1,2}[.-/]\d{1,2}[.-/]\d{2,4})'
    ]
}

def extract_biomarkers(text):
    """
    Extract biomarkers from text using NLP and regex
    
    Args:
        text (str): OCR extracted text
        
    Returns:
        tuple: (dict of biomarkers, study date, patient_info)
    """
    biomarkers = {}
    patient_info = {
        'patient_surname': None,
        'patient_name': None,
        'patient_patronymic': None,
        'patient_dob': None,
        'patient_number': None
    }
    
    # Extract study date
    study_date = extract_date(text)
    
    # Extract patient information
    extract_patient_info(text, patient_info)
    
    # Try using spaCy for Russian text
    if nlp_ru:
        doc_ru = nlp_ru(text)
        biomarkers_ru = extract_biomarkers_spacy(doc_ru)
        biomarkers.update(biomarkers_ru)
    
    # Try using spaCy for English text
    if nlp_en:
        doc_en = nlp_en(text)
        biomarkers_en = extract_biomarkers_spacy(doc_en)
        biomarkers.update(biomarkers_en)
    
    # Use regex as a fallback
    biomarkers_regex = extract_biomarkers_regex(text)
    
    # Merge results, preferring spaCy results over regex when available
    for key, value in biomarkers_regex.items():
        if key not in biomarkers:
            biomarkers[key] = value
    
    # Calculate if values are abnormal
    for biomarker in biomarkers.values():
        if 'reference_range' in biomarker and biomarker['reference_range']:
            min_val = biomarker['reference_range'].get('min')
            max_val = biomarker['reference_range'].get('max')
            if min_val is not None and max_val is not None:
                biomarker['is_abnormal'] = biomarker['value'] < min_val or biomarker['value'] > max_val
    
    return biomarkers, study_date, patient_info

def extract_patient_info(text, patient_info):
    """
    Extract patient information from text
    
    Args:
        text (str): OCR extracted text
        patient_info (dict): Dictionary to store patient information
        
    Returns:
        dict: Updated patient information
    """
    # Extract full name
    for pattern in PATIENT_PATTERNS['full_name']:
        match = re.search(pattern, text)
        if match:
            full_name = match.group(1).strip()
            name_parts = full_name.split()
            if len(name_parts) >= 1:
                patient_info['patient_surname'] = name_parts[0]
            if len(name_parts) >= 2:
                patient_info['patient_name'] = name_parts[1]
            if len(name_parts) >= 3:
                patient_info['patient_patronymic'] = name_parts[2]
            break
    
    # Extract medical number
    for pattern in PATIENT_PATTERNS['medical_number']:
        match = re.search(pattern, text)
        if match:
            patient_info['patient_number'] = match.group(1).strip()
            break
    
    # Extract date of birth
    for pattern in PATIENT_PATTERNS['date_of_birth']:
        match = re.search(pattern, text)
        if match:
            dob_str = match.group(1).strip()
            try:
                # Try different date formats
                for fmt in ['%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%y', '%d-%m-%y', '%d/%m/%y']:
                    try:
                        dob = datetime.strptime(dob_str, fmt).date()
                        patient_info['patient_dob'] = dob
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.error(f"Error parsing date of birth: {str(e)}")
            break
    
    return patient_info

def extract_biomarkers_spacy(doc):
    """
    Extract biomarkers using spaCy NER
    
    Args:
        doc: spaCy document
        
    Returns:
        dict: Dictionary of biomarkers
    """
    biomarkers = {}
    
    # Look for entities that might be biomarkers
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PRODUCT', 'CHEMICAL', 'GPE']:
            # Check if this entity matches any known biomarker
            for biomarker_name, patterns in BIOMARKER_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, ent.text, re.IGNORECASE):
                        # Look for numbers near this entity
                        for token in doc:
                            if token.is_digit or token.like_num:
                                # Check if this token is close to the entity
                                if abs(token.i - ent.start) < 10:
                                    try:
                                        value = float(token.text.replace(',', '.'))
                                        
                                        # Look for unit
                                        unit_text = doc[token.i:token.i+5].text
                                        unit = extract_unit(unit_text)
                                        
                                        # Look for reference range
                                        range_text = doc[token.i:token.i+20].text
                                        reference_range = extract_reference_range(range_text)
                                        
                                        biomarkers[biomarker_name] = {
                                            'name': biomarker_name,
                                            'value': value,
                                            'unit': unit,
                                            'reference_range': reference_range
                                        }
                                        break
                                    except ValueError:
                                        continue
    
    return biomarkers

def extract_biomarkers_regex(text):
    """
    Extract biomarkers using regex patterns
    
    Args:
        text (str): OCR extracted text
        
    Returns:
        dict: Dictionary of biomarkers
    """
    biomarkers = {}
    
    # Split text into lines for better context
    lines = text.split('\n')
    
    for line in lines:
        for biomarker_name, patterns in BIOMARKER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Try to extract value
                    value_match = re.search(r'(\d+[.,]?\d*)', line)
                    if value_match:
                        try:
                            value = float(value_match.group().replace(',', '.'))
                            
                            # Find unit
                            unit = extract_unit(line)
                            
                            # Extract reference range if available
                            ref_range = extract_reference_range(line)
                            
                            biomarker_data = {
                                'value': value,
                                'unit': unit
                            }
                            
                            if ref_range:
                                biomarker_data.update(ref_range)
                            
                            biomarkers[biomarker_name] = biomarker_data
                            break
                        except ValueError:
                            pass
    
    return biomarkers

def extract_unit(text):
    """
    Extract unit from text
    
    Args:
        text (str): Text to extract unit from
        
    Returns:
        str: Extracted unit or None
    """
    for unit, patterns in UNIT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return unit
    
    return None

def extract_reference_range(text):
    """
    Extract reference range from text
    
    Args:
        text (str): Text to extract reference range from
        
    Returns:
        dict: Dictionary with min and max values or empty dict
    """
    # Look for patterns like "reference: 0.8-1.2" or "norm: 0.8-1.2" or just "0.8-1.2"
    range_match = re.search(r'(?:референс|норма|norm|ref|reference)[^0-9]*(\d+[.,]?\d*)\s*[-–—]\s*(\d+[.,]?\d*)', text, re.IGNORECASE)
    
    if not range_match:
        # Try to find just the range without labels
        range_match = re.search(r'[\(\[\{]?\s*(\d+[.,]?\d*)\s*[-–—]\s*(\d+[.,]?\d*)[\)\]\}]?', text)
    
    if range_match:
        try:
            min_val = float(range_match.group(1).replace(',', '.'))
            max_val = float(range_match.group(2).replace(',', '.'))
            return {
                'reference_range_min': min_val,
                'reference_range_max': max_val
            }
        except (ValueError, IndexError):
            pass
    
    return {}

def extract_date(text):
    """
    Extract study date from text
    
    Args:
        text (str): OCR extracted text
        
    Returns:
        datetime.date: Extracted date or None
    """
    # Look for date patterns
    for line in text.split('\n'):
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                try:
                    # Check format based on the pattern
                    if pattern.startswith(r'(\d{4})'):
                        # YYYY/MM/DD
                        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    else:
                        # DD/MM/YYYY
                        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                        
                        # Handle 2-digit years
                        if year < 100:
                            year += 2000 if year < 50 else 1900
                    
                    # Validate date
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        return datetime(year, month, day).date()
                except (ValueError, IndexError):
                    pass
    
    # Look for date keywords
    date_keywords = ['дата', 'date', 'от', 'from']
    for line in text.split('\n'):
        for keyword in date_keywords:
            if keyword in line.lower():
                for pattern in DATE_PATTERNS:
                    match = re.search(pattern, line)
                    if match:
                        try:
                            # Check format based on the pattern
                            if pattern.startswith(r'(\d{4})'):
                                # YYYY/MM/DD
                                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                            else:
                                # DD/MM/YYYY
                                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                                
                                # Handle 2-digit years
                                if year < 100:
                                    year += 2000 if year < 50 else 1900
                            
                            # Validate date
                            if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                                return datetime(year, month, day).date()
                        except (ValueError, IndexError):
                            pass
    
    return None
