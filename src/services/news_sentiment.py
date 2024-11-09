import os
import re

from textblob import TextBlob
from repo.db_repo import DatabaseManager
from utils import Crawl

class NewsSentiment:
    def __init__(self, db_manager:DatabaseManager):
        self.db_manager = db_manager
        self.crawler = Crawl(self.db_manager)
    
    def get_articles(self):
        articles_without_sentiment = self.db_manager.fetch_records(
            "select top 2* from newstracker where NewsTickersSentiment  is null and IsSentimentProcessed =0", ())
        return articles_without_sentiment
    
    def get_stocks(self):
        stocks = self.db_manager.fetch_records('select name, ticker from companies', ())
        return stocks
    
    def keywords_in_article(self,  article, keyword_tuples):
        keyword_mentions = {}

        # Loop over each tuple of keywords
        for keyword1, keyword2 in keyword_tuples:
            # Check if either of the keywords is present in the content
            if re.search(r'\b' + re.escape(keyword1) + r'\b', article, re.IGNORECASE) or re.search(r'\b' + re.escape(keyword2) + r'\b', content, re.IGNORECASE):
                keyword_mentions[(keyword1, keyword2)] = True
            else:
                keyword_mentions[(keyword1, keyword2)] = False

        return keyword_mentions
    
    def keywords_in_article_sentiment(self,  content, keyword_tuples):
        analysis_results = {}
        for keyword1, keyword2 in keyword_tuples:
            if (keyword1, keyword2) not in analysis_results:
                if re.search(r'\b' + re.escape(keyword1) + r'\b', content, re.IGNORECASE) or \
                    re.search(r'\b' + re.escape(keyword2) + r'\b', content, re.IGNORECASE):
                    blob = TextBlob(content)
                    sentiment = blob.sentiment.polarity
                    analysis_results[(keyword1, keyword2)] = sentiment
                    break

        return analysis_results

    def extract_sentiment_and_ticker(self, url, keywords):
        page = self.crawler.download_page(url)
        page_text = page.get_text()
        print(page_text)
        keyword_in_article = self.keywords_in_article_sentiment(page_text, keywords)
        return keyword_in_article
    
    def process(self):
        articles_without_sentiment = self.get_articles()
        print('articles without sentiment \n',articles_without_sentiment)
        keywords = self.get_stocks()
        print(keywords)
        print('processing articles \n')

        result = []
        if articles_without_sentiment:
            for article in articles_without_sentiment:
                id = article[0]
                keyword_sentiment = self.extract_sentiment_and_ticker(article[3], keywords)
                keyword_sentiment['id'] = id
                result.append(keyword_sentiment)
        return result

