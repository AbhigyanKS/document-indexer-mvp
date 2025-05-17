import boto3
import json
import base64
import logging
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
load_dotenv()  # This MUST be called before accessing os.getenv(...)


# logging Setup 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helps to retrive Credentials from AWS Secrets Manager
def get_secret():
    print("inside get_secret")
    """
    Retrieves a secret value from AWS Secrets Manager using ARN.
    
    Args:
        secret_arn (str): The ARN of the secret to retrieve.
        region_name (str): The AWS region where the secret is stored.
    
    Returns:
        dict or bytes: The secret value, either as a JSON-decoded dictionary or as raw binary data.
    """
    region_name = os.getenv("REGION_NAME")
    secret_arn = os.getenv("SECRETS_MANAGER_ARN_ID")
    print(f"Loaded region: {region_name}")
    print(f"Loaded secret ARN: {secret_arn}")

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        # Attempt to retrieve the secret value
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_arn
        )
    except ClientError as e:
        logger.error(f"ClientError when trying to get the secret value: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error when trying to get the secret value: {e}")
        raise

    # Extract and return the secret
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        logger.info("Secret String retrieved successfully.")
        try:
            secret_dict = json.loads(secret)
            return secret_dict
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise
    elif 'SecretBinary' in get_secret_value_response:
        decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
        logger.info("Decoded binary secret retrieved successfully.")
        return decoded_binary_secret
    else:
        logger.error("No secret string or binary data found in response.")
        raise ValueError("No secret string or binary data found in response.")