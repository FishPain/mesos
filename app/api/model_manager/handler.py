import os, uuid
from werkzeug.datastructures import FileStorage

from app.core.SagemakerManager import SagemakerManager
from app.constants import SageMakerConstants as sm_constants
from app.constants import AppConstants as app_constants
from app.models.models import MLModel


def download_from_s3(model_uuid: str) -> dict:
    bucket_name = sm_constants.BUCKET_NAME
    role = sm_constants.ROLE
    sm = SagemakerManager(bucket_name, role)

    try:
        s3_file_path = MLModel.get_record_by_uuid(model_uuid).s3_url

        # Download the model from S3
        local_filepath_list = sm.download_from_s3(s3_file_path)
        resp = {
            "uuid": model_uuid,
            "local_filepath_list": local_filepath_list,
        }

    except Exception as e:
        raise Exception(f"Failed to download the model from S3: {e}")

    return resp


def push_to_s3(model: FileStorage) -> dict:
    bucket_name = sm_constants.BUCKET_NAME
    role = sm_constants.ROLE
    sm = SagemakerManager(bucket_name, role)
    resp = dict()

    if not (model):
        raise Exception("Invalid file format. Please upload a tar.gz file")

    # Define the directory to save the uploaded file
    upload_dir = app_constants.MODEL_UPLOAD_TEMP_DIR

    # Create the directory if it doesn't exist
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Save the uploaded file to the specified directory
    file_path = os.path.join(upload_dir, model.filename)
    model.save(file_path)

    # Upload the file to S3
    try:
        s3_path = sm.upload_to_s3(file_path, model.filename)
        model_type = "tensorflow"  # TODO: Add support for other model types
        model_uuid = MLModel.save_model_to_db(
            model_name=model.filename, model_type=model_type, s3_url=s3_path
        )

        resp = {
            "uuid": model_uuid,
            "path": s3_path,
        }

    except Exception as e:
        raise Exception(f"Failed to upload the model to S3: {e}")

    finally:
        # clean up the file
        os.remove(file_path)

    return resp


def delete_from_s3(model_uuid: str) -> dict:
    bucket_name = sm_constants.BUCKET_NAME
    role = sm_constants.ROLE
    sm = SagemakerManager(bucket_name, role)

    try:
        # Delete the model from S3
        resp = sm.delete_model(model_uuid)
    except Exception as e:
        raise Exception(f"Failed to delete the model from S3: {e}")

    return resp
