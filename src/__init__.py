from datetime import datetime
import os
from flask import Flask, g
from src.repo.db_repo import DatabaseManager
from src.routes import webpage
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from src.utils import Crawl
from flask_apscheduler import APScheduler


app = Flask(__name__)
app.register_blueprint(webpage)

db_manager = DatabaseManager(
    server=os.getenv('DB_SERVER'),
    database=os.getenv('DB_NAME'),
    username=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS')
)

@app.before_request
def before_request():
    g.db_manager = db_manager

def background_process():
    crawler = Crawl(db_manager)
    print("Starting crawler: {0}".format(datetime.now().strftime('%d-%m-%Y, %H:%M:%S')))
    crawler.crawl_news()
    print("Completed crawler: {0}".format(datetime.now().strftime('%d-%m-%Y, %H:%M:%S')))

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# scheduler = BackgroundScheduler()
# scheduler.add_job(background_process, 'interval', minutes=5)
# scheduler.start()
scheduler = APScheduler()
scheduler.api_enabled=True
scheduler.init_app(app)

#@scheduler.task('interval', id='news_job', hours=1, minutes=0)
#Every hour on the clock monday - friday hour='*/1', 
@scheduler.task('cron', id='news_job', hour='*/1', day_of_week='1-5')
def background_process():
    crawler = Crawl(db_manager)
    print("> Starting crawler: {0}".format(datetime.now().strftime('%d-%m-%Y, %H:%M:%S')))
    #crawler.crawl_news()
    print("> Completed crawler: {0}".format(datetime.now().strftime('%d-%m-%Y, %H:%M:%S')))


scheduler.start()
# @app.teardown_appcontext
# def shutdown_scheduler(exception=None):
#     scheduler.shutdown()
