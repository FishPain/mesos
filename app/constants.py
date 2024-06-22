from dotenv import load_dotenv

load_dotenv()


class AppConstants:
    SERVICE_NAME = "Harbourfront Python REST API Template"
    SERVICE_DESCRIPTION = "You can change this description in /app/constants.py"
    API_VERSION = "v1"
    MODEL_UPLOAD_TEMP_DIR = "temp/models/upload/lpd.pt"
    MODEL_DOWNLOAD_TEMP_DIR = "temp/models/download/lpd.pt"
    VIDEO_UPLOAD_TEMP_DIR = "temp/videos/upload"
    VIDEO_DOWNLOAD_TEMP_DIR = "temp/videos/download"
    DATA_UPLOAD_TEMP_DIR = "temp/data/upload/plate_numbers_with_info.json"
    DATA_DOWNLOAD_TEMP_DIR = "temp/data/download/"


class JobConstants:
    UPLOAD_MODEL = "upload_model"
    DOWNLOAD_MODEL = "download_model"
    TRAIN_MODEL = "train_model"
    DEPLOY_MODEL = "deploy_model"
    DELETE_MODEL = "delete_model"
    START_INFERENCE = "start_inference"
