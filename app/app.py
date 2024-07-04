import json, os

from flask import Flask, Blueprint, render_template

from flask_cors import CORS
from flask_restx import Api

from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.constants import AppConstants as app_constants


def init_app():
    """Spawns the application"""

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    CORS(app)

    # Set Flask configuration
    app.config["ERROR_404_HELP"] = False

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")

    # Register application endpoints using Blueprint
    blueprint = Blueprint("api", __name__, url_prefix=f"/{app_constants.API_VERSION}")

    api = Api(
        blueprint,
        title=app_constants.SERVICE_NAME,
        version=app_constants.API_VERSION,
        description=app_constants.SERVICE_DESCRIPTION,
        doc="/docs/",
    )

    register_namespaces(api)
    app.register_blueprint(blueprint)

    # Register error handlers
    @app.errorhandler(HTTPException)
    def app_error_handler(err):
        response = err.get_response()
        response.data = json.dumps(
            {
                "code": err.code,
                "name": err.name,
                "message": err.description,
            }
        )
        response.content_type = "application/json"
        return response

    @api.errorhandler(HTTPException)
    def api_error_handler(err):
        data = {
            "code": err.code,
            "name": err.name,
        }
        return data, err.code

    # Add route for the HTML page
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/management")
    def console():
        return render_template("console.html")

    @app.route("/game")
    def game():
        return render_template("game.html")

    os.makedirs(os.path.dirname(app_constants.VIDEO_DOWNLOAD_TEMP_DIR), exist_ok=True)
    os.makedirs(os.path.dirname(app_constants.VIDEO_UPLOAD_TEMP_DIR), exist_ok=True)

    return app


def register_namespaces(app_api):
    """Adds the namespaces to the application"""
    from app.api.inference.controller import ns as inference_namespace
    from app.api.user.controller import ns as user_namespace
    from app.api.erp.controller import ns as erp_namespace
    from app.api.video.controller import ns as video_namespace

    app_api.add_namespace(inference_namespace, path="/api/inference")
    app_api.add_namespace(user_namespace, path="/api/user")
    app_api.add_namespace(erp_namespace, path="/api/erp")
    app_api.add_namespace(video_namespace, path="/api/video")

    # Add more namespaces here
