import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import concurrent.futures
import time

from src.processing.image_processor import preprocess_image
from src.processing.ocr_engine import extract_text
from src.processing.nlp_analyzer import extract_biomarkers
from src.database.models import db, BloodTest, Biomarker
from src.database.operations import save_blood_test, get_all_blood_tests, get_biomarker_history

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_key_for_testing')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///blood_test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

def process_file(filepath, filename):
    """Process a single file and save results to database"""
    try:
        # Process the uploaded file
        preprocessed_image = preprocess_image(filepath)
        extracted_text = extract_text(preprocessed_image)
        biomarkers, study_date, patient_info = extract_biomarkers(extracted_text)
        
        # Save to database
        blood_test_id = save_blood_test(biomarkers, study_date, filename, patient_info)
        return blood_test_id, None
    except Exception as e:
        logger.error(f"Error processing file {filename}: {str(e)}")
        return None, str(e)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Legacy route for single file upload"""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        blood_test_id, error = process_file(filepath, filename)
        if error:
            flash(f'Error processing file: {error}')
            return redirect(url_for('index'))
        else:
            flash('File successfully processed and data extracted')
            return redirect(url_for('view_result', test_id=blood_test_id))
    else:
        flash('File type not allowed')
        return redirect(url_for('index'))

@app.route('/upload_files', methods=['POST'])
def upload_files():
    """Route for bulk file upload and processing"""
    if 'files[]' not in request.files:
        flash('No files part')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        flash('No selected files')
        return redirect(url_for('index'))
    
    # Limit to 100 files
    if len(files) > 100:
        flash('Too many files. Maximum is 100 files per upload.')
        return redirect(url_for('index'))
    
    # Track results
    processed_count = 0
    error_count = 0
    processed_ids = []
    
    # Process each file
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            blood_test_id, error = process_file(filepath, filename)
            if error:
                error_count += 1
                logger.error(f"Failed to process {filename}: {error}")
            else:
                processed_count += 1
                processed_ids.append(blood_test_id)
        else:
            error_count += 1
            logger.warning(f"Skipped file {file.filename} - not allowed type")
    
    # Provide feedback to user
    if processed_count > 0:
        flash(f'Successfully processed {processed_count} files. Failed: {error_count}')
        if len(processed_ids) == 1:
            return redirect(url_for('view_result', test_id=processed_ids[0]))
        else:
            return redirect(url_for('results'))
    else:
        flash('No files were processed successfully')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort_by = request.args.get('sort_by', 'study_date')
    sort_order = request.args.get('sort_order', 'desc')
    
    blood_tests = get_all_blood_tests(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
    return render_template('results.html', blood_tests=blood_tests, sort_by=sort_by, sort_order=sort_order)

@app.route('/result/<int:test_id>')
def view_result(test_id):
    blood_test = BloodTest.query.get_or_404(test_id)
    biomarkers = Biomarker.query.filter_by(blood_test_id=test_id).all()
    return render_template('result.html', blood_test=blood_test, biomarkers=biomarkers)

@app.route('/biomarker_history/<biomarker_name>')
def biomarker_history(biomarker_name):
    patient_surname = request.args.get('patient_surname')
    patient_number = request.args.get('patient_number')
    
    history = get_biomarker_history(biomarker_name, patient_surname, patient_number)
    return render_template('biomarker_history.html', 
                          biomarker_name=biomarker_name,
                          patient_surname=patient_surname,
                          patient_number=patient_number,
                          history=history)

@app.route('/api/blood-tests', methods=['GET'])
def api_get_blood_tests():
    sort_by = request.args.get('sort_by', 'study_date')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    blood_tests_pagination = get_all_blood_tests(page=page, per_page=per_page, sort_by=sort_by, sort_order=sort_order)
    blood_tests = blood_tests_pagination.items
    
    result = []
    for test in blood_tests:
        biomarkers = Biomarker.query.filter_by(blood_test_id=test.id).all()
        test_data = {
            'id': test.id,
            'filename': test.filename,
            'study_date': test.study_date.isoformat() if test.study_date else None,
            'created_at': test.created_at.isoformat(),
            'patient': {
                'surname': test.patient_surname,
                'name': test.patient_name,
                'patronymic': test.patient_patronymic,
                'full_name': test.get_full_name(),
                'dob': test.patient_dob.isoformat() if test.patient_dob else None,
                'number': test.patient_number
            },
            'biomarkers': [{
                'name': biomarker.name,
                'value': biomarker.value,
                'unit': biomarker.unit,
                'is_abnormal': biomarker.is_abnormal
            } for biomarker in biomarkers]
        }
        result.append(test_data)
    
    return jsonify({
        'results': result,
        'pagination': {
            'page': blood_tests_pagination.page,
            'per_page': blood_tests_pagination.per_page,
            'total': blood_tests_pagination.total,
            'pages': blood_tests_pagination.pages
        }
    })

@app.route('/api/blood-test/<int:test_id>', methods=['GET'])
def api_get_blood_test(test_id):
    blood_test = BloodTest.query.get_or_404(test_id)
    biomarkers = Biomarker.query.filter_by(blood_test_id=test_id).all()
    result = {
        'id': blood_test.id,
        'filename': blood_test.filename,
        'study_date': blood_test.study_date.isoformat() if blood_test.study_date else None,
        'created_at': blood_test.created_at.isoformat(),
        'patient': {
            'surname': blood_test.patient_surname,
            'name': blood_test.patient_name,
            'patronymic': blood_test.patient_patronymic,
            'full_name': blood_test.get_full_name(),
            'dob': blood_test.patient_dob.isoformat() if blood_test.patient_dob else None,
            'number': blood_test.patient_number
        },
        'biomarkers': [{
            'name': biomarker.name,
            'value': biomarker.value,
            'unit': biomarker.unit,
            'is_abnormal': biomarker.is_abnormal
        } for biomarker in biomarkers]
    }
    return jsonify(result)

@app.route('/api/biomarker_history/<biomarker_name>', methods=['GET'])
def api_biomarker_history(biomarker_name):
    patient_surname = request.args.get('patient_surname')
    patient_number = request.args.get('patient_number')
    
    history = get_biomarker_history(biomarker_name, patient_surname, patient_number)
    result = [{
        'date': date.isoformat() if date else None,
        'value': value,
        'unit': unit,
        'is_abnormal': is_abnormal
    } for date, value, unit, is_abnormal in history]
    
    return jsonify(result)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Create database tables - updated for newer Flask versions
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    # Create tables before running the app
    create_tables()
    app.run(debug=os.getenv('FLASK_DEBUG', 'True') == 'True', host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
