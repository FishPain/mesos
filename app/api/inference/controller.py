from flask import request
from flask_restx import Namespace, Resource, fields
from app.api.inference.handler import (
    start_inference_by_model_uuid,
    get_inference_by_uuid,
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
            os.makedirs(
                os.path.dirname(app_constants.VIDEO_DOWNLOAD_TEMP_DIR), exist_ok=True
            )
            resp = start_inference_by_model_uuid()
            file.save(f"{app_constants.VIDEO_DOWNLOAD_TEMP_DIR}/{resp.get('uuid')}.mp4")
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

        if inference_uuid:
            # Implement model deletion logic here
            return "Inference job stopped successfully", 200
        else:
            return "Inference job not found", 400
