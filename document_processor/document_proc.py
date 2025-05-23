from pdfminer.high_level import extract_text
from indexer.opensearch import index_document
from datetime import datetime
from PIL import Image
import time
import gc
import pytesseract

import os
from io import BytesIO
import fitz
import base64


def image_to_base64(image_path, max_base64_size=5242880):
    try:
        with Image.open(image_path) as img:
            img_byte_array = BytesIO()
            img.save(img_byte_array, format="JPEG")
            base64_encoded = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
            if len(base64_encoded) <= max_base64_size:
                return base64_encoded

            quality = 90
            while len(base64_encoded) > max_base64_size and quality > 10:
                new_dimensions = (int(img.width * 0.8), int(img.height * 0.8))
                img = img.resize(new_dimensions, Image.Resampling.LANCZOS)
                img_byte_array = BytesIO()
                img.save(img_byte_array, format="JPEG", quality=quality)
                base64_encoded = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')
                quality -= 10

            if len(base64_encoded) > max_base64_size:
                print(f"Image too large, reducing quality to {quality}")
                img_byte_array = BytesIO()
                img.save(img_byte_array, format="JPEG", quality=10)
                base64_encoded = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

            return base64_encoded
    except Exception as e:
        print(f"Error resizing image: {str(e)}")
        return None
    
def pdf_to_images(pdf_path, output_directory, dpi=300):
    """
    Optimized function to convert PDF to images with reduced memory usage.
    """
    try:
        # Check if the PDF file exists
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return []

        # Create the output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)

        print(f"Processing PDF: {pdf_path}")

        image_paths = []

        # Open the PDF file
        with fitz.open(pdf_path) as pdf_document:
            if len(pdf_document) == 0:
                print(f"PDF file has no pages: {pdf_path}")
                return []

            # Process one page at a time to minimize memory usage
            for page_number in range(len(pdf_document)):
                page = pdf_document.load_page(page_number)

                # Calculate the zoom factor based on the desired DPI
                zoom = dpi / 72  # 72 is the default DPI for PDF
                matrix = fitz.Matrix(zoom, zoom)

                # Create an image of the page
                image = page.get_pixmap(matrix=matrix)

                # Save the image and add its path to the list
                image_filename = f"page_{page_number + 1}.png"
                image_path = os.path.join(output_directory, image_filename)
                image.save(image_path)
                image_paths.append(image_path)

                # Explicitly delete the image object to free memory
                del image

                # Optionally, call garbage collection to release unused memory
                gc.collect()

        print(f"Converted {len(image_paths)} pages to images in {output_directory}")
        return image_paths

    except fitz.FileDataError as e:
        print(f"Error reading PDF file: {str(e)}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return []



import cv2
import pytesseract

def preprocess_image(image_path):
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Optionally apply denoising
    # thresh = cv2.medianBlur(thresh, 3)

    return thresh

def extract_text_from_image_using_ocr(image_path):
    try:
        preprocessed_image = preprocess_image(image_path)
        text = pytesseract.image_to_string(preprocessed_image , lang='eng')
        return text
    except Exception as e:
        print(f"[ERROR] OCR failed for {image_path}: {e}")
        return ""
    
def extract_text_from_image(image_path):
    start_time = time.time()  # Start measuring time
    print(f"inside extract_text_from_image: {image_path}")
    """
    Extracts text content from an image using Textract.

    Args:
        image_path (str): The file path to the image.

    Returns:
        str: The extracted text content from the image, or an empty string if an error occurs.
    """
    try:
        # Read text from image using OCR
        text = extract_text_from_image_using_ocr(image_path)
        end_time = time.time()  # End measuring time
        execution_time = end_time - start_time  # Calculate execution time
        print(f"extract_text_from_image function execution time: {execution_time:.2f} seconds - helper.py")
        return text
    except Exception as e:
        print(f"Error reading image {image_path}: {e}")
        return ""
from concurrent.futures import ThreadPoolExecutor    
def process_pdf_and_extract_text(pdf_path, output_folder):
    """
        Converts a PDF to images and extracts text content from each image using multithreading. The function
        first converts each page of the provided PDF into an image. Then, it uses multithreading to process 
        each image in parallel, extracting the text content. After all pages have been processed, the text is 
        sorted by page order and concatenated to form a single document.

        Args:
            pdf_path (str): The file path to the PDF document that needs to be processed.
            output_folder (str): The folder where the converted images will be saved.

        Returns:
            str: The concatenated text content from all the pages of the PDF, ordered by page.
    """
    # Step 1: Convert PDF to images
    image_paths = pdf_to_images(pdf_path, output_folder)

    # Step 2: Use multithreading to process each image and extract text
    document_content = []
    def extract_with_index(index, path):
        return (index, extract_text_from_image(path))
    # Create a ThreadPoolExecutor to handle parallel extraction
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(extract_with_index, i, path) for i, path in enumerate(image_paths)]
        for future in futures:
            document_content.append(future.result())

    # Sort the document content by page index and concatenate
    document_content.sort(key=lambda x: x[0])  # Sort by the page index (the first element of the tuple)
    
    # Concatenate the text from each page in the correct order
    final_document = ''.join([text for _, text in document_content])
    print(f"[DEBUG] Final OCR-extracted text: {final_document[:500]}")
    return final_document

# SQ_AF_1.167 - SQ_AF_1.172
def is_scanned_document(pdf_path):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        print(f"[DEBUG] Page {page_num} text length: {len(text)}")
        if text.strip():  # If there's any text, it's likely a raw PDF
            return False
    return True  # If no text found on any page, it's likely a scanned document

def extract_text_from_pdf_using_ocr(pdf_path):
    doc = fitz.open(pdf_path)
    text_content = ""
    print(f"[DEBUG] Extracted raw text: {text_content[:500]}")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_content += page.get_text("text")
    return text_content

def extract_text_from_file(file_path: str) -> str:
    """
    Determines if the PDF is scanned or digital and extracts text accordingly.
    """
    if is_scanned_document(file_path):
        print(f"🔎 Scanned document detected: {file_path}")
        return process_pdf_and_extract_text(file_path, output_folder="converted_images")
    else:
        print(f"📝 Digital document detected: {file_path}")
        return extract_text_from_pdf_using_ocr(file_path)

    
'''def encode_file_to_base64(file_path):
    """Reads and encodes file in base64 format."""
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    return extract_text(file_path)

def extract_text_from_image(file_path):
    """Extract text from an image file using OCR."""
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)

def extract_text_from_file(file_path):
    """Determine file type and call appropriate text extraction function."""
    file_extension = file_path.split('.')[-1].lower()
    print("Processing file:", file_path)

    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['jpeg', 'jpg', 'png']:
        return extract_text_from_image(file_path)
    return None  # Return None if unsupported file type

def process_document_llm_output(file_path, user_id, llm_json_response):
    """
    Indexes structured LLM response into OpenSearch.
    """
    document_data = {
        "title": os.path.basename(file_path),
        "user_id": user_id,
        "category": llm_json_response.get("category", "unknown"),
        "document_type": llm_json_response.get("document_type", "unknown"),
        "content": llm_json_response.get("content", {}),
        "uploaded_at": datetime.utcnow().isoformat()
    }

    index_document(document_data)
    print(f"✅ Indexed LLM-processed document: {file_path}")

'''