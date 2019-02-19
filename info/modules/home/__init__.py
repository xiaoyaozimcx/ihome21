from flask import Blueprint

home_blue = Blueprint('home_blue', __name__)
static_blue = Blueprint('static_blue', __name__, static_folder='../../static/html', static_url_path='')

from . import views