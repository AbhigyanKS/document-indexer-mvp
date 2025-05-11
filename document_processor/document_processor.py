from pdfminer.high_level import extract_text
from indexer.opensearch import index_document
from datetime import datetime
from PIL import Image
import pytesseract
import os

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

    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension in ['jpeg', 'jpg', 'png']:
        return extract_text_from_image(file_path)
    return None  # Return None if unsupported file type

def categorize_document(text):
    """Categorize document based on keywords found in the text."""
    keywords = {
        'birth_certificate': ['birth', 'certificate', 'born', 'date of birth'],
        'drivers_license': ['driver', 'license', 'drivers', 'vehicle'],
        'social_security': ['ssn', 'social security', 'social', 'number'],
    }

    text = text.lower()
    for category, words in keywords.items():
        if any(word in text for word in words):
            return category
    return 'other'




def process_document(file_path, extracted_text, user_id, category):
    """
    Process document and send data to be indexed in OpenSearch
    """
    document_data = {
        "title": file_path.split("/")[-1],  # or however you want to handle the title
        "content": extracted_text,
        "user_id": user_id,
        "category": category,
        "uploaded_at": datetime.utcnow().isoformat()  # Get current time for uploaded_at
    }

    # Index the document
    index_document(document_data)
    print(f"Document {file_path} indexed successfully.")
