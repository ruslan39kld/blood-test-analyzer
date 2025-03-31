# Blood Test Analyzer

An AI system for analyzing biochemical blood test results from scanned documents.

## Project Overview

This system automatically recognizes key indicators from blood biochemical test results presented as digital images or text files. It uses OpenCV for image processing, OCR for text extraction, and NLP methods (spaCy) for entity recognition to extract key biomarkers, units of measurement, and study dates from scanned biochemical blood tests.

The extracted data is stored in a structured way in a PostgreSQL database, which can be accessed through a web interface.

## Key Features

- Automatic extraction of key biomarkers from scanned blood tests
- Recognition of units of measurement and study dates
- Structured storage in PostgreSQL database
- Web interface for data access and management

## Key Indicators

The system extracts the following biomarkers:
- Total cholesterol
- LDL-C
- HDL-C
- Triglycerides
- Creatinine
- Urea
- Uric acid
- ALT
- AST
- CPC
- Total bilirubin
- Potassium
- Sodium
- Glucose
- Glycated haemoglobin
- TTG
- Т4

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up PostgreSQL database
4. Configure the application settings
5. Run the application

## Usage

### Web Interface

Start the web server:
```
python app.py
```

Access the web interface at http://localhost:5000

### API

The system also provides a REST API for integration with other systems.

## Technologies Used

- Python
- OpenCV for image processing
- Tesseract OCR for text recognition
- spaCy for NLP and entity extraction
- PostgreSQL for data storage
- Flask for web interface
