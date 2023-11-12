from flask import jsonify

from app.api import api
from app.api.exceptions import APIError


@api.errorhandler(APIError)
def api_error(e):
    return jsonify(e.get_data()), e.status_code


@api.errorhandler(415)
def unsupported_media_type_error():
    return jsonify({'errors': ['request content type must be application/json']}), 415


@api.errorhandler(404)
def unsupported_media_type_error():
    return jsonify({}), 404
