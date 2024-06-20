from flask import request
from flask_restx import Namespace, Resource, fields

ns = Namespace("erp", description="erp operations")

erp_model = ns.model(
    "erp",
    {
        "distance": fields.Integer(
            description="The distance of the car from the emergency vehicle"
        ),
        "lane": fields.Integer(description="The lane of the emergency vehicle"),
    },
)

update_message_data_parser = ns.parser()
update_message_data_parser.add_argument(
    "distance",
    type=int,
    required=True,
    help="The distance of the car from the emergency vehicle",
)
update_message_data_parser.add_argument(
    "lane",
    type=int,
    required=True,
    help="The lane of the emergency vehicle",
)


@ns.route("/update_data")
class ERP(Resource):
    settings = {
        "distance": 500,
        "lane": 1,
    }

    @ns.response(200, "Success", erp_model)
    def get(self):
        """Get the distance and lane of the emergency vehicle"""
        resp = self.settings
        return {
            "message": "Message Data retrieved successfully",
            "result": resp,
        }, 200

    @ns.expect(update_message_data_parser)
    def post(self):
        """Update the distance and lane of the emergency vehicle"""
        self.settings["distance"] = request.args.get("distance")
        self.settings["lane"] = request.args.get("lane")
        resp = self.settings
        return {
            "message": "Message Data updated successfully",
            "result": resp,
        }, 200
