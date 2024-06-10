from flask import request
from flask_restx import Namespace, Resource, fields
from app.core.SagemakerManager import SagemakerManager
from app.constants import SageMakerConstants as sm_constants
from app.core.auth_utils import get_header
from app.models.models import ModelRegistryModel, InferenceModel, UserModel, MLModel
import uuid

import json

ns = Namespace("Inference", description="Inference operations")

get_parser = ns.parser()
get_parser.add_argument("uuid", type=str, required=True, help="The inference UUID")

upload_parser = ns.parser()
upload_parser.add_argument(
    "inference_data", location="files", type="file", required=True, help="A json file"
)
upload_parser.add_argument(
    "uuid",
    type=str,
    required=True,
    help="The model registry UUID",
)

delete_parser = ns.parser()
delete_parser.add_argument("uuid", type=str, required=True, help="The inference UUID")

inference_model = ns.model(
    "Inference",
    {
        "message": fields.String(description="Response message"),
        "uuid": fields.String(description="Inference UUID"),
    },
)

inference_result_model = ns.model(
    "InferenceResult",
    {
        "inference_uuid": fields.String(description="Inference UUID"),
        "status": fields.String(description="Inference status"),
        "inference": fields.String(description="Inference result"),
    },
)


@ns.route("/")
class Inference(Resource):
    @ns.expect(get_parser)
    @ns.response(200, "Success", inference_result_model)
    def get(self):
        """Get inference result by inference id"""
        inference_uuid = request.args.get("uuid")
        inference_result = {
            "inference_uuid": inference_uuid,
            "status": "completed",
            "inference": "This is a dummy inference result",
        }
        return {
            "message": "Inference Results retrieved successfully",
            "inference_result": inference_result,
        }, 200

    # flask status code 200
    @ns.expect(upload_parser)
    @ns.response(200, "Success", inference_model)
    def post(self):
        """Post an inference job"""
        # Process the JSON data here
        # You can perform any required operations
        # json data in the format of {"inputs": ndarray.tolist()}
        json_data = request.files.get("inference_data")
        model_registry_uuid = request.args.get("uuid")
        sm = SagemakerManager(
            role=sm_constants.ROLE,
            bucket_name=sm_constants.BUCKET_NAME,
        )

        if json_data and model_registry_uuid and json_data.filename.endswith(".json"):
            model_endpoint = ModelRegistryModel.get_record_by_uuid(
                model_registry_uuid
            ).model_endpoint

            base = "https://"
            host = "runtime.sagemaker.ap-southeast-1.amazonaws.com"
            canonical_uri = f"/endpoints/{model_endpoint}/invocations"

            inference_endpoint = base + host + canonical_uri

            # load the json data from the file
            json_data = json.load(json_data)

            if "inputs" not in json_data:
                return "Invalid JSON data provided", 400
            
            json_string = json.dumps(json_data)
            
            header = get_header(payload=json_string, endpoint=model_endpoint)
            
            response = sm.invoke_endpoint(
                endpoint=inference_endpoint, payload=json_string, header=header
            )

            dummy_user_uuid = UserModel.get_user_uuid_by_email("dummyUser@dummy.com")
            if dummy_user_uuid is None:
                raise Exception("User does not exist")

            inference_status = "pending"

            if response.status_code == 200:
                inference_status = "completed"

            inference_uuid = InferenceModel.save_inference_to_db(
                user_uuid=dummy_user_uuid,
                model_registry_uuid=model_registry_uuid,
                inference_status=inference_status,
            )

            response_data = {
                "message": "Inference job posted successfully",
                "body": {
                    "uuid": inference_uuid,
                    "status": response.status_code,
                    "inference_result": json.loads(response.text),
                },
            }
            return response_data, 200
        else:
            return "No JSON data provided", 400

    @ns.expect(delete_parser)
    @ns.response(200, "Success")
    def delete(self):
        """Delete the inference based on inference id and returns 200 if success"""
        inference_uuid = request.args.get("uuid")

        if inference_uuid:
            # Implement model deletion logic here
            return "Inference job stopped successfully", 200
        else:
            return "Inference job not found", 400
