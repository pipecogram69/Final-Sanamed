from flask import Blueprint

profesional_bp = Blueprint('profesional', __name__, url_prefix='/profesional')

from . import routes