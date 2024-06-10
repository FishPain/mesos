from sagemaker.utils import name_from_base
from sagemaker.local import LocalSession
from sagemaker.tensorflow import TensorFlowModel
from sagemaker.model import FrameworkModel
from app.constants import AppConstants as app_constants
import requests


class SagemakerManager:
    def __init__(self, bucket_name, role):
        self.bucket_name = bucket_name
        self.role = role
        self.local_session = LocalSession()

    def download_from_s3(self, s3_file_path: str) -> list:
        # this is a filter that will only download items within this directory
        # TODO: Fix complete the implementation.
        # currently the download does not work.
        model_folder_path = s3_file_path.split("/")[-2]

        local_path_list = self.local_session.download_data(
            path=app_constants.MODEL_DOWNLOAD_TEMP_DIR,
            bucket=self.bucket_name,
            key_prefix=model_folder_path,
        )

        return local_path_list

    def upload_to_s3(self, model_path, model_name):
        compilation_job_name = name_from_base(model_name)
        input_model_path = self.local_session.upload_data(
            path=model_path, bucket=self.bucket_name, key_prefix=compilation_job_name
        )
        print("S3 path for input model: {}".format(input_model_path))
        return input_model_path

    def create_model(self, model_path, model_type):
        if model_type == "tensorflow":
            model = TensorFlowModel(
                model_data=model_path, role=self.role, framework_version="2.10"
            )
        elif model_type == "pytorch":
            pass
        elif model_type == "sklearn":
            pass
        else:
            raise ValueError("Invalid model type")
        return model

    def deploy_model(self, model: FrameworkModel, instance_type, endpoint_name=None):
        predictor = model.deploy(
            initial_instance_count=1,
            instance_type=instance_type,
            endpoint_name=endpoint_name,
        )
        return predictor

    def invoke_endpoint(self, endpoint, payload, header):
        response = requests.post(endpoint, data=payload, headers=header)
        return response

    def predict(self, predictor, data):
        return predictor.predict(data)
