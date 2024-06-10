import os
from dotenv import load_dotenv

load_dotenv()


class AppConstants:
    SERVICE_NAME = "Harbourfront Python REST API Template"
    SERVICE_DESCRIPTION = "You can change this description in /app/constants.py"
    API_VERSION = "v1"
    MODEL_UPLOAD_TEMP_DIR = "temp/models/upload/"
    MODEL_DOWNLOAD_TEMP_DIR = "temp/models/download/"


class SageMakerConstants:
    BUCKET_NAME = os.environ.get("BUCKET_NAME", "s3://sagemaker")
    ROLE = os.environ.get("IAM_ROLE", "arn:aws:iam::123456789")
    REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-1")


class InstanceType:
    CPU = "ml.m4.xlarge"
    GPU = "ml.p2.xlarge"
    INFERENCE = "ml.t2.medium"
    LOCAL = "local"
