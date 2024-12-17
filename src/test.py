import os
from repo.db_repo import DatabaseManager
from services.news_sentiment import NewsSentiment


if __name__=='__main__':
    db_manager = DatabaseManager(
        server=os.getenv('DB_SERVER'),
        database=os.getenv('DB_NAME'),
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS')
    )
    newsSentiment = NewsSentiment(db_manager)
    keywords = newsSentiment.get_stocks()
    print('got keywords')
    result = newsSentiment.extract_sentiment_and_ticker('https://businessday.ng/companies/article/access-bank-to-acquire-100-stake-in-24-years-old-south-africas-bidvest-bank/',
                                                keywords)
    print(result)

    #testing the sentiment to get the right prompt 
    #clnewsSentiment.process()