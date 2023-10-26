from flask import jsonify

from app.api import api
from app.api.exceptions import APIError


@api.errorhandler(APIError)
def api_error(e):
    return jsonify(e.data), e.status_code
