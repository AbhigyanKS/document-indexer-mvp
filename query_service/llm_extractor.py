import boto3
import os
import base64
import json
from query_service.secret_manager import get_secret
from dotenv import load_dotenv
from document_processor.document_proc import (
    is_scanned_document,
    process_pdf_and_extract_text,
    extract_text_from_pdf_using_ocr
)
import time
import mimetypes


load_dotenv()

# Load credentials
creds = get_secret()

# Initialize Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))

def encode_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_text_from_file(file_path: str, temp_image_folder: str = "converted_images") -> str:
    """
    Entry point that selects appropriate extraction method based on PDF type.
    Do not modify document_proc.py – instead adapt to its structure.
    """
    if is_scanned_document(file_path):
        return process_pdf_and_extract_text(file_path, temp_image_folder)
    else:
        return extract_text_from_pdf_using_ocr(file_path)

def extract_info_with_llm(document_text: str, filename: str) -> dict:
    """
    Extracts structured information from unstructured document text using a Bedrock-hosted LLM.
    """
    system_prompt = "You are a document data extractor."

    user_prompt = f"""
The following is the extracted text of an identity document.
Filename: {filename}

Extract the information in this exact JSON format:
{{
  "category": "Identity Document",
  "document_type": "<Type>",
  "content": {{
    "Field1": "Value1",
    "Field2": "Value2"
  }}
}}

Be accurate. Extract only what is visible. Do not make up values. Output valid JSON only.

Document text:
{document_text}
"""

    model_id = os.getenv("AWS_MODEL_ID")
    if not model_id:
        raise ValueError("AWS_MODEL_ID environment variable not set")

    body = {
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.3,
        "anthropic_version": os.getenv("ANTHROPIC_VERSION", "bedrock-2023-05-31")
    }

    response = bedrock.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )

    raw_output = json.loads(response["body"].read().decode())

    try:
        extracted_text = raw_output["content"][0]["text"].strip()
        if extracted_text.startswith("```json"):
            extracted_text = extracted_text[len("```json"):].strip()
        if extracted_text.endswith("```"):
            extracted_text = extracted_text[:-3].strip()

        return json.loads(extracted_text)

    except Exception as e:
        print("[ERROR] Could not parse model output:", raw_output)
        raise e


'''
def validate_document_type_summary_using_llm(image_path: str) -> str:
    """
    Summarizes the content of a document image using a Bedrock-hosted LLM.
    """
    print("inside validate_document_type_summary_using_llm")
    mime_type, _ = mimetypes.guess_type(image_path)
    try:
        start_time = time.time()

        base64_string = encode_file_to_base64(image_path)

        output_response = {
            "summary": "<A short summary of the document image, which should contain all the necessary information about the document image including all the names of the document holder (should specify whether the extracted names are first name/last names). This summary should contain all the text content in the document. Do not miss any information from the document>"
        }

        system_prompt = f"""
        You are a document validation expert. Your task is to analyze the document image and summarize the document image in short manner. The incoming document type image will be provided to you. You will have to validate the document content accurately and return the JSON response. While returning the document summary in specific to the name return the First name first followed by last name. The output JSON response is as follows: {output_response}
        """

        prompt = f"""
        <NOTE>
            1. Strictly do not explain what is in the document image. Just provide the summary of the document image.
            2. Strictly EXTRACT and SUMMARISE All details present in the document.
            3. Make sure to use this output response format: {output_response}
            4. The output response should be in JSON format.
            5. Make sure summary should not contain any special characters like ("," or ";") or any special characters.
            6. If there are dates something like this "05/26/2022" in the provided image then make sure to remove the "/" from the date.
            7. Please do not explain the solution above and below the response.
            8. For paystub document type, Transcribe the EXACT text that contains the company's complete physical address.
        </NOTE>   
        """

        model_id = os.getenv("AWS_MODEL_ID")
        if not model_id:
            raise ValueError("AWS_MODEL_ID environment variable not set")

        request_body = {
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type or "image/png",
                                "data": base64_string,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        },
                    ]
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.6,
            "anthropic_version": os.getenv("ANTHROPIC_VERSION", "bedrock-2023-05-31"),
        }

        request_body_json = json.dumps(request_body)
        request_body_bytes = request_body_json.encode("utf-8")

        response = bedrock.invoke_model(body=request_body_bytes, modelId=model_id)
        response_body = json.loads(response["body"].read())

        llm_res = response_body["content"][0]["text"]
        print(llm_res, "LLM Response for validate_document_type_summary_using_llm")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"validate_document_type_summary_using_llm function execution time: {execution_time:.2f} seconds")

        return llm_res

    except Exception as e:
        print(f"Error in validate_document_type_summary_using_llm: {str(e)}")
        return ""
        '''