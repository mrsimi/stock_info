from flask import Blueprint
from src.controllers.home_controller import home_bp

webpage = Blueprint('/', __name__)

webpage.register_blueprint(home_bp)