from flask import Blueprint, g, render_template

from src.services.news_service import NewsService

home_bp = Blueprint('home_bp', __name__, 
                    template_folder='templates')

@home_bp.route('/')
def home():
    news_service = NewsService(g.db_manager)
    records, has_next_page = news_service.get_news()

    return render_template('home.html', records=records)