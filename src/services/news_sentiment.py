import json
import os
import re
import google.generativeai as genai
from src.repo.db_repo import DatabaseManager
from src.utils import Crawl
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import nltk
from transformers import pipeline
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"



class NewsSentiment:
    def __init__(self, db_manager:DatabaseManager):
        nltk.download('punkt')
        nltk.download('punkt_tab')
        self.db_manager = db_manager
        self.crawler = Crawl(self.db_manager)
        genai.configure(api_key=os.getenv('API_KEY'))
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")

    def __get_articles(self):
        articles_without_sentiment = self.db_manager.fetch_records(
            "select top 10 id, link, title from NewsTracker with (nolock) where \
                IsSentimentProcessed =0 order by date desc", ())
        return articles_without_sentiment
    
    def get_stocks(self):
        stocks = self.db_manager.fetch_records('select keywords, ticker from companies', ())
        return stocks
    
    def emphasize_keywords(self, text, keywords, repetition_factor=2):
        """
        Increases the frequency of specified keywords in the text by repeating them.
        This could help the summarizer give more attention to these keywords.
        """
        words = text.split()
        emphasized_text = []

        for word in words:
            emphasized_text.append(word)
            if word.lower() in keywords:
                # Repeat the keyword to make it appear more frequently
                for _ in range(repetition_factor - 1):  
                    emphasized_text.append(word)
        
        return " ".join(emphasized_text)

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
        # for keyword1, keyword2 in keyword_tuples:
        #     if (keyword1, keyword2) not in analysis_results:
        #         if re.search(r'\b' + re.escape(keyword1) + r'\b', content, re.IGNORECASE) or \
        #             re.search(r'\b' + re.escape(keyword2) + r'\b', content, re.IGNORECASE):
                    
        #             prompt = """
        #                 Given this text {0}
        #                 Determine the if it related to any of this text {1}, {2}. 
        #                 If it is determine the sentiment around positive, negative or neutral
        #                 and also a short description of the reason for this decision in JSON format. 

        #                 Use this JSON schema:
        #                 Response = {'sentiment': str, 'reason': str}
        #                 Return: Response
        #             """.format(content, keyword1, keyword2)
        #             blob = TextBlob(content)
        #             sentiment = blob.sentiment.polarity
        #             analysis_results[keyword2] = round(sentiment, 2)
        #             break
        result = {}
        for keyword1, keyword2 in keyword_tuples:
            if re.search(r'\b' + re.escape(keyword1) + r'\b', content, re.IGNORECASE) or \
                    re.search(r'\b' + re.escape(keyword2) + r'\b', content, re.IGNORECASE):
                    
                    prompt = "Given this text " + content \
                        + "Determine the if it related to any of these company " + keyword1 + ", " + keyword2 +" in relation to their company performance."\
                        +  """
                                If it is not related or the article reports a status of several stocks return sentiment as notrelated 
                                else determine the sentiment around positive, negative or neutral
                                and also a short description of the reason for this decision in JSON format. 

                                Use this JSON schema:
                                Response = {'sentiment': str, 'reason': str}
                                Return: Response
                            """
                    try:
                        res = self.gemini_model.generate_content(prompt,
                                                                    generation_config=genai.GenerationConfig(
                                                                        response_mime_type="application/json"
                                                                    ))

                        if res.text:
                            res_json = json.loads(res.text)
                            if res_json['sentiment'] != 'notrelated':
                                res_json['ticker'] = keyword2
                                result = res_json
                                break
                    except Exception as err:
                        print('error while trying to process ', err)
                        return None

        return result
    
    def string_in_text(self, text, string_list):
        text = text.lower()  
        for s in string_list:
            if s.lower().strip() in text:  
                return True 
        return False 

    def keywords_in_article_sentiment_v3(self, news, title, keyword_tuples):
        pipe = pipeline("text-classification", model="ProsusAI/finbert")
        result = {}
        parser = PlaintextParser.from_string(news, Tokenizer("english"))

        summarizer = LsaSummarizer(Stemmer("english"))
        summarizer.stop_words = get_stop_words("english")

        summary = summarizer(parser.document, 3)
        text_summary = [str(sentence) for sentence in summary]
        text_summary = ''.join(text_summary)

        #print(text_summary)
        for keyword1, keyword2 in keyword_tuples:
            string_list = keyword1.split('|')
            #print(string_list)
            if self.string_in_text(title, string_list):
                sentiment_result = pipe(text_summary)
                result['ticker'] = keyword2
                result['reason'] = text_summary
                result['sentiment'] = sentiment_result[0]['label']
        return result
    
    def __dict_to_string(self, d):
        if len(d.keys()) == 1: 
            return ''.join(d.keys()), ''.join(map(str, d.values())) 
        return '|'.join(d.keys()), '|'.join(map(str, d.values())) 

    def extract_sentiment_and_ticker(self, url,title, keywords):
        page = self.crawler.download_page(url)
        page_text = page.get_text()
        #print(page_text)
        keyword_in_article = self.keywords_in_article_sentiment_v3(page_text, title, keywords)
        return keyword_in_article
    
    def process(self):
        articles_without_sentiment = self.__get_articles()
        #print('articles without sentiment \n',articles_without_sentiment)
        keywords = self.get_stocks()
        #print(keywords)
        print('processing_articles \n')

        if articles_without_sentiment:
            for article in articles_without_sentiment:
                id = article[0]
                keyword_sentiment = self.extract_sentiment_and_ticker(article[1], article[2], keywords)   #{'accesscorp' : '0.08'}
                #print(keyword_sentiment)
                if keyword_sentiment is not None:
                    if keyword_sentiment.keys():
                        update_query = """
                            update newstracker 
                            set NewsTickers = ?,
                                NewsTickersSentiment = ?,
                                AISummary = ?,
                                IsSentimentProcessed = 1
                            where id = ? 
                        """
                        self.db_manager.single_inserts(update_query, 
                                                    (keyword_sentiment['ticker'], keyword_sentiment['sentiment'], keyword_sentiment['reason'], id))
                    else:
                        delete_query = """
                            delete from newstracker 
                            where id = ? 
                        """
                        self.db_manager.single_inserts(delete_query, (id,))
        
        print('processed_{}_articles'.format(len(articles_without_sentiment)))

