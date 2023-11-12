from flask import Blueprint

api = Blueprint('api', __name__)

from app.api import views
from app.api import error_views
