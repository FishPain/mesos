from flask import request
from flask_restx import Namespace, Resource, fields
from app.models.models import ModelRegistryModel, JobsModel
from app.api.model_registry.handler import clean_up_model_resources, register_model

ns = Namespace("Model Registry", description="Model registry operations")

get_parser = ns.parser()
get_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

get_fields = ns.model(
    "Model",
    {
        "message": fields.String(description="Response message"),
        "body": fields.Nested(
            ns.model(
                "Body",
                {
                    "uuid": fields.String(description="Model UUID"),
                    "local_filepath_list": fields.List(
                        fields.String,
                        description="Local file path that stores the downloaded model",
                    ),
                },
            )
        ),
    },
)


post_parser = ns.parser()
post_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

post_fields = ns.model(
    "Model",
    {
        "message": fields.String(description="Response message"),
        "body": fields.Nested(
            ns.model(
                "Body",
                {
                    "uuid": fields.String(description="Model UUID"),
                    "path": fields.String(description="S3 path"),
                },
            )
        ),
    },
)


delete_parser = ns.parser()
delete_parser.add_argument(
    "uuid", type=str, required=True, help="The model registry UUID"
)


@ns.route("/")
class ModelRegistry(Resource):
    @ns.expect(get_parser)
    @ns.response(200, "Success", get_fields)
    def get(self):
        """
        Get Model Registry Infomation by UUID
        """
        model_registry_uuid = request.args.get("uuid")
        record = ModelRegistryModel.get_record_by_uuid(model_registry_uuid)

        resp = {
            "message": "Model retrieved successfully",
            "body": {
                "uuid": record.model_uuid,
                "model_version": record.model_version,
                "endpoint_name": record.model_endpoint,
                "status": record.model_status,
            },
        }

        return resp, 200

    @ns.expect(post_parser)
    @ns.response(200, "Success", post_fields)
    def post(self):
        """
        Create a sagemaker endpoint for the model
        """
       
        model_uuid = request.args.get("uuid")

        task_id = register_model(model_uuid)

        resp = {
            "message": "Model endpoint creation started",
            "body": {"task_id": task_id},
        }
        return resp, 200

    @ns.expect(delete_parser)
    @ns.response(200, "Success")
    def delete(self):
        """
        Delete a model from s3 and db by UUID
        """
        model_uuid = request.args.get("uuid")

        if model_uuid:
            endpoint_name = ModelRegistryModel.get_record_by_uuid(
                model_uuid
            ).model_endpoint

            try:
                clean_up_model_resources(model_uuid, endpoint_name)
            except Exception as e:
                return {"message": f"Failed to delete the endpoint: {e}"}, 500

            return "Model endpoint deleted successfully", 200
        else:
            return "Model UUID is missing", 400


get_status_parser = ns.parser()
get_status_parser.add_argument("uuid", type=str, required=True, help="The job UUID")

get_status_fields = ns.model(
    "Model",
    {
        "message": fields.String(description="Response message"),
        "body": fields.Nested(
            ns.model(
                "Body",
                {
                    "uuid": fields.String(description="Model UUID"),
                    "status": fields.String(
                        description="Local file path that stores the downloaded model"
                    ),
                },
            )
        ),
    },
)


@ns.route("/status")
class ModelRegistryStatus(Resource):
    @ns.expect(get_status_parser)
    @ns.response(200, "Success", get_status_fields)
    def get(self):
        """
        Get Model Registry Job by UUID
        """
        job_uuid = request.args.get("uuid")
        record = JobsModel.get_record_by_uuid(job_uuid)

        resp = {
            "message": "Job status retrieved successfully",
            "body": {"uuid": job_uuid, "status": record.job_status},
        }

        return resp, 200
