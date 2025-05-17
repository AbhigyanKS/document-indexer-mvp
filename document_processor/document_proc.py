from pdfminer.high_level import extract_text
from indexer.opensearch import index_document
from datetime import datetime
from PIL import Image
import pytesseract

import os
import base64



def encode_file_to_base64(file_path):
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

