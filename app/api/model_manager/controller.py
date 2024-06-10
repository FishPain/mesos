from flask import request
from flask_restx import Namespace, Resource, fields
from app.api.model_manager.handler import push_to_s3, download_from_s3

ns = Namespace("Model Manager", description="Model management operations")

get_parser = ns.parser()
get_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

upload_parser = ns.parser()
upload_parser.add_argument(
    "file", location="files", type="file", required=True, help="A tar.gz file"
)

delete_parser = ns.parser()
delete_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

get_model_fields = ns.model(
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

post_model_fields = ns.model(
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


@ns.route("/")
class ModelManager(Resource):
    @ns.expect(get_parser)
    @ns.response(200, "Success", get_model_fields)
    def get(self):
        """
        Get model s3 path by UUID from db
        """
        model_uuid = request.args.get("uuid")
        resp = download_from_s3(model_uuid)
        return {"message": "Model retrieved successfully", "body": resp}, 200

    @ns.expect(upload_parser)
    @ns.response(200, "Success", post_model_fields)
    def post(self):
        """
        Upload a model to S3 and returns the model UUID and S3 path
        """
        uploaded_file = request.files["file"]
        try:
            resp = push_to_s3(uploaded_file)
        except Exception as e:
            return {"message": f"Failed to upload the model to S3: {e}"}, 500

        return {"message": "File uploaded successfully", "body": resp}, 200

    @ns.expect(delete_parser)
    @ns.response(200, "Success")
    def delete(self):
        """
        Delete a model from s3 and db by UUID
        """
        model_uuid = request.args.get("uuid")

        if model_uuid:
            # Implement model deletion logic here
            return "Model deleted successfully", 200
        else:
            return "Model UUID is missing", 400


register_parser = ns.parser()
register_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

post_register_fields = ns.model(
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
