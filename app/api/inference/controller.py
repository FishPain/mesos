from flask import request
from flask_restx import Namespace, Resource, fields
from app.api.inference.handler import (
    start_inference_by_model_uuid,
    get_inference_by_uuid,
    get_latest_inference_job,
    get_all_inference_job,
    delete_inference,
)
from app.constants import AppConstants as app_constants
import os
import uuid

ns = Namespace("Inference", description="Inference operations")

get_parser = ns.parser()
get_parser.add_argument("uuid", type=str, required=True, help="The inference UUID")

upload_parser = ns.parser()
upload_parser.add_argument(
    "inference_data",
    location="files",
    type="FileStorage",
    required=True,
    help="File containing inference data",
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

latest_inference_result_model = ns.model(
    "LatestInferenceResult",
    {
        "inference_uuid": fields.String(description="Latest Inference UUID"),
        "status": fields.String(description="Latest Inference status"),
        "inference": fields.String(description="Latest Inference result"),
    },
)


@ns.route("/")
class Inference(Resource):
    @ns.expect(get_parser)
    @ns.response(200, "Success", inference_result_model)
    def get(self):
        """Get inference result by inference id"""
        inference_uuid = request.args.get("uuid")
        resp = get_inference_by_uuid(inference_uuid)
        inference_result = {
            "inference_uuid": inference_uuid,
            "status": resp.get("status"),
            "inference": resp.get("inference_result"),
        }
        return {
            "message": "Inference Results retrieved successfully",
            "inference_result": inference_result,
        }, 200

    @ns.expect(upload_parser)
    @ns.response(200, "Success", inference_model)
    def post(self):
        """Post an inference job"""
        file = request.files.get("inference_data")

        if file:
            temp_uuid = str(uuid.uuid4())
            temp_file_path = f"{app_constants.VIDEO_DOWNLOAD_TEMP_DIR}/{temp_uuid}.mp4"
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
            file.save(temp_file_path)
            resp = start_inference_by_model_uuid(temp_uuid)
            response_data = {
                "message": "Inference job posted successfully",
                "body": resp,
            }
            return response_data, 200
        return {"message": "No file provided"}, 400

    @ns.expect(delete_parser)
    @ns.response(200, "Success")
    def delete(self):
        """Delete the inference based on inference id and returns 200 if success"""
        inference_uuid = request.args.get("uuid")

        try:
            resp = delete_inference(inference_uuid)
            response_data = {
                "message": "Inference job deleted successfully",
                "body": resp,
            }
            return response_data, 200
        except Exception as e:

            return "Inference job not found", 400


@ns.route("/latest")
class InferenceData(Resource):  # Changed class name to inherit from Resource
    @ns.response(200, "Success", latest_inference_result_model)
    def get(self):
        """Get the latest inference job result"""
        resp = get_latest_inference_job()
        return {
            "message": "Latest inference result retrieved successfully",
            "latest_inference_result": resp,
        }, 200


@ns.route("/all")
class InferenceData(Resource):  # Changed class name to inherit from Resource
    @ns.response(200, "Success", latest_inference_result_model)
    def get(self):
        """Get the latest inference job result"""
        resp = get_all_inference_job()
        return {
            "message": "Latest inference result retrieved successfully",
            "inference_results": resp,
        }, 200
