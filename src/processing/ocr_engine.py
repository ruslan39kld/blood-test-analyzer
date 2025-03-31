import pytesseract
import cv2
import numpy as np
import logging
import os
from PIL import Image
from dotenv import load_dotenv
from src.processing.nlp_analyzer import DATE_PATTERNS

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Set Tesseract path if specified in environment or if not in PATH
tesseract_path = os.getenv('TESSERACT_PATH')
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    logger.info(f"Using Tesseract from: {tesseract_path}")

def extract_text(image):
    """
    Extract text from image using OCR
    
    Args:
        image (numpy.ndarray): Preprocessed image
        
    Returns:
        str: Extracted text
    """
    try:
        logger.info("Extracting text with Tesseract OCR")
        
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image)
        
        # Extract text with Tesseract
        text = pytesseract.image_to_string(pil_image, lang='rus+eng')
        
        if not text.strip():
            logger.warning("No text extracted, trying with different preprocessing")
            # Try with different preprocessing if no text was extracted
            inverted = cv2.bitwise_not(image)
            text = pytesseract.image_to_string(inverted, lang='rus+eng')
        
        logger.info(f"Extracted {len(text)} characters")
        return text
    
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise

def extract_text_with_layout(image):
    """
    Extract text with layout information
    
    Args:
        image (numpy.ndarray): Preprocessed image
        
    Returns:
        dict: Dictionary with text and layout information
    """
    try:
        # Get detailed information including bounding boxes
        data = pytesseract.image_to_data(image, lang='rus+eng', output_type=pytesseract.Output.DICT)
        
        # Process the data
        result = []
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 60:  # Filter by confidence
                text = data['text'][i]
                if text.strip():  # Skip empty text
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    result.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'conf': data['conf'][i],
                        'line_num': data['line_num'][i],
                        'block_num': data['block_num'][i]
                    })
        
        return result
    
    except Exception as e:
        logger.error(f"Error extracting text with layout: {str(e)}")
        raise

def extract_tables(image):
    """
    Extract tables from image
    
    Args:
        image (numpy.ndarray): Preprocessed image
        
    Returns:
        list: List of extracted tables as text
    """
    try:
        # Use Tesseract's built-in table extraction
        tables_data = pytesseract.image_to_data(image, lang='rus+eng', output_type=pytesseract.Output.DICT, config='--psm 6')
        
        # Group by block_num to get tables
        blocks = {}
        for i in range(len(tables_data['text'])):
            if tables_data['text'][i].strip():
                block_num = tables_data['block_num'][i]
                if block_num not in blocks:
                    blocks[block_num] = []
                blocks[block_num].append({
                    'text': tables_data['text'][i],
                    'line_num': tables_data['line_num'][i],
                    'par_num': tables_data['par_num'][i],
                    'word_num': tables_data['word_num'][i]
                })
        
        # Convert blocks to tables
        tables = []
        for block_num, words in blocks.items():
            # Sort by line and word number
            words.sort(key=lambda x: (x['line_num'], x['word_num']))
            
            # Group by line
            lines = {}
            for word in words:
                line_num = word['line_num']
                if line_num not in lines:
                    lines[line_num] = []
                lines[line_num].append(word['text'])
            
            # Convert to table format
            table_text = '\n'.join([' '.join(line) for line in lines.values()])
            tables.append(table_text)
        
        return tables
    
    except Exception as e:
        logger.error(f"Error extracting tables: {str(e)}")
        raise
