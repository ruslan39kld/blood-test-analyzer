import cv2
import numpy as np
import os
import logging
import tempfile
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

def preprocess_image(file_path):
    """
    Preprocess the input image for better OCR results
    
    Args:
        file_path (str): Path to the input file (image or PDF)
        
    Returns:
        numpy.ndarray: Preprocessed image ready for OCR
    """
    try:
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Handle PDF files
        if file_ext == '.pdf':
            logger.info(f"Converting PDF to image: {file_path}")
            pages = convert_from_path(file_path, 400)  # Increased DPI for better quality
            if not pages:
                raise ValueError("Failed to convert PDF to image")
            # Use the first page
            pil_image = pages[0]
            # Apply PIL enhancements
            pil_image = enhance_image_quality(pil_image)
            # Convert PIL to OpenCV format
            image = np.array(pil_image)
            # Convert to BGR if it's in RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            # Read image file
            logger.info(f"Reading image file: {file_path}")
            # First try with PIL for better enhancement options
            try:
                pil_image = Image.open(file_path)
                pil_image = enhance_image_quality(pil_image)
                # Convert PIL to OpenCV format
                image = np.array(pil_image)
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            except Exception as e:
                logger.warning(f"Failed to process with PIL, falling back to OpenCV: {str(e)}")
                image = cv2.imread(file_path)
            
        if image is None:
            raise ValueError(f"Failed to read image from {file_path}")
        
        # Resize if image is too small
        h, w = image.shape[:2]
        min_dimension = 1800  # Minimum dimension for good OCR
        if h < min_dimension or w < min_dimension:
            scale_factor = max(min_dimension / h, min_dimension / w)
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            logger.info(f"Resized image from {w}x{h} to {new_w}x{new_h}")
            
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding instead of global Otsu
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Noise removal with bilateral filter (preserves edges better)
        denoised = cv2.bilateralFilter(binary, 9, 75, 75)
        
        # Additional denoising for severely noisy images
        denoised = cv2.fastNlMeansDenoising(denoised, None, 10, 7, 21)
        
        # Deskew the image if it's tilted
        denoised = deskew_image(denoised)
        
        # Sharpen the image to make text more defined
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        # Dilation to make text more visible but with smaller kernel
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.dilate(sharpened, kernel, iterations=1)
        
        # Save the preprocessed image for debugging
        debug_path = os.path.join(os.path.dirname(file_path), 'preprocessed_' + os.path.basename(file_path))
        cv2.imwrite(debug_path, processed)
        logger.info(f"Saved preprocessed image to {debug_path}")
        
        return processed
    
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        raise

def enhance_image_quality(pil_image):
    """
    Enhance image quality using PIL
    
    Args:
        pil_image (PIL.Image): Input PIL image
        
    Returns:
        PIL.Image: Enhanced image
    """
    # Convert to RGB if it's not
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # Apply a series of enhancements
    # Increase contrast
    enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = enhancer.enhance(1.5)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(pil_image)
    pil_image = enhancer.enhance(2.0)
    
    # Adjust brightness if needed
    enhancer = ImageEnhance.Brightness(pil_image)
    pil_image = enhancer.enhance(1.1)
    
    # Apply unsharp mask filter for better edge definition
    pil_image = pil_image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    return pil_image

def deskew_image(image):
    """
    Deskew the image if it's tilted
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        numpy.ndarray: Deskewed image
    """
    try:
        # Find all contours
        contours, _ = cv2.findContours(~image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest contour
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Find the minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            
            # Determine if the angle needs adjustment
            if angle < -45:
                angle = 90 + angle
            
            # If the angle is significant, rotate the image
            if abs(angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                logger.info(f"Deskewed image by {angle} degrees")
                return rotated
    except Exception as e:
        logger.warning(f"Error during deskew: {str(e)}")
    
    # Return original if deskew failed or wasn't needed
    return image

def detect_table_areas(image):
    """
    Detect table areas in the image
    
    Args:
        image (numpy.ndarray): Input image
        
    Returns:
        list: List of bounding rectangles for detected tables
    """
    # Make a copy of the image
    img_copy = image.copy()
    
    # Find all contours
    contours, _ = cv2.findContours(~img_copy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by size and shape to find table-like structures
    table_rects = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)
        
        # Tables typically have a large area and a specific aspect ratio
        if area > 5000 and 0.5 < aspect_ratio < 5:
            table_rects.append((x, y, w, h))
    
    return table_rects

def extract_roi(image, roi_type):
    """
    Extract region of interest based on type
    
    Args:
        image (numpy.ndarray): Input image
        roi_type (str): Type of ROI to extract ('header', 'table', 'footer')
        
    Returns:
        numpy.ndarray: Extracted ROI
    """
    height, width = image.shape[:2]
    
    if roi_type == 'header':
        # Extract top 20% of the image
        return image[0:int(height*0.2), 0:width]
    elif roi_type == 'table':
        # Extract middle 60% of the image
        return image[int(height*0.2):int(height*0.8), 0:width]
    elif roi_type == 'footer':
        # Extract bottom 20% of the image
        return image[int(height*0.8):height, 0:width]
    else:
        return image
