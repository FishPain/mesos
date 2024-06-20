from flask import request, make_response
from flask_restx import Namespace, Resource, fields
from app.core.s3_utils import get_s3_file
import os

ns = Namespace("video", description="video operations")

get_parser = ns.parser()
get_parser.add_argument("uuid", type=str, required=True, help="The inference UUID")

@ns.route("/preprocessed")
class PreprocessedVideo(Resource):
    @ns.expect(get_parser)
    def get(self):
        """Serve the preprocessed video file from S3 with support for range requests"""
        inference_uuid = request.args.get("uuid")
        range_header = request.headers.get("Range", None)
        bucket_name = os.getenv("BUCKET_NAME")
        file_key = f"mesos/{inference_uuid}.mp4"
        file_content, content_type, content_range, content_length = get_s3_file(
            bucket_name, file_key, range_header
        )

        if file_content:
            response = make_response(file_content.read())
            response.headers.set("Content-Type", content_type)
            response.headers.set(
                "Content-Disposition", "inline; filename=input_video.mp4"
            )
            response.headers.set("Accept-Ranges", "bytes")
            if content_range:
                response.headers.set("Content-Range", content_range)
                response.headers.set("Content-Length", str(content_length))
                response.status_code = 206  # Partial Content
            else:
                response.headers.set("Content-Length", str(content_length))
            return response
        else:
            return {"message": "File not found"}, 404


@ns.route("/postprocessed")
class PostprocessedVideo(Resource):
    def get(self):
        """Serve the postprocessed video file from S3"""
        file_content, content_type = get_s3_file(
            "temp/videos/upload/postprocessed_annotated_video.mp4"
        )
        if file_content:
            response = make_response(file_content)
            response.headers.set("Content-Type", content_type)
            return response
        else:
            return {"message": "File not found"}, 404
