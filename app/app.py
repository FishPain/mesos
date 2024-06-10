import json, os

from flask import Flask, Blueprint
from flask_cors import CORS
from flask_restx import Api

from celery import Celery

from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.constants import AppConstants as app_constants
from app.constants import SageMakerConstants as sm_constants
from app.core.SagemakerManager import SagemakerManager

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

    return app


def register_namespaces(app_api):
    """Adds the namespaces to the application"""
    from app.api.model_manager.controller import ns as model_manager_namespace
    from app.api.inference.controller import ns as inference_namespace
    from app.api.user.controller import ns as user_namespace
    from app.api.model_registry.controller import ns as model_registry_namespace

    app_api.add_namespace(model_manager_namespace, path="/api/model_manager")
    app_api.add_namespace(inference_namespace, path="/api/inference")
    app_api.add_namespace(user_namespace, path="/api/user")
    app_api.add_namespace(model_registry_namespace, path="/api/model_registry")

    # Add more namespaces here