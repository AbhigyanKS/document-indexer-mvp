import boto3
import os
import base64
import json
from query_service.secret_manager import get_secret
from dotenv import load_dotenv
from document_processor.document_proc import extract_text_from_file
load_dotenv()


# Load credentials if needed (or just rely on AWS CLI setup)
creds = get_secret()

# Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))

def encode_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

import boto3
import os
import base64
import json
from query_service.secret_manager import get_secret
from dotenv import load_dotenv

load_dotenv()

# Load secrets
creds = get_secret()

# Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))

def encode_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def extract_info_with_llm(document_text: str, filename: str) -> dict:
   
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
            {
                "role": "user",
                "content": user_prompt
            }
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
        # Remove triple backticks if present
        extracted_text = raw_output["content"][0]["text"].strip()
        if extracted_text.startswith("```json"):
            extracted_text = extracted_text[len("```json"):].strip()
        if extracted_text.endswith("```"):
            extracted_text = extracted_text[:-3].strip()

        return json.loads(extracted_text)

    except Exception as e:
        print("[ERROR] Could not parse model output:", raw_output)
        raise e
