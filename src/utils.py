import csv
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import os
import json
from src.repo.db_repo import DatabaseManager
from dotenv import load_dotenv
from dateutil import parser

load_dotenv()


class Crawl:
    def __init__(self, db_manager:DatabaseManager):
        self.db_manager = db_manager
        
    
    def _get_config(self):
        saved_config = self.db_manager.fetch_records("select * from sourceconfig", ())
        configs = [config[1] for config in saved_config]
        return configs
    
    def download_page(self, url):
        page = requests.get(url)
        if  page.status_code == 200:
            try: 
                soup = BeautifulSoup(page.content, "html.parser")
                #print(soup.prettify())
                return soup
            except Exception as err:
                print(f'Error occured while trying to parse to BS4 - {0}', err)
        else:
            return None
    
    def process_news(self, soup:BeautifulSoup, config):
        articles = soup.find_all(config['article_tag'])
        result = []
        if len(articles) == 0:
            articles = soup.find_all(class_=config['article_tag'])

        last_date = ''
        for article in articles:
            post_title = article.find(class_=config['title_class'])
            post_link = article.find(class_=config['link_class'])
            post_date = article.find(class_=config['date_class'])
            article_dict = {}
            if post_link:
                link = post_link.find('a').get('href')

                if post_date is not None:
                    article_dict['title'] = post_title.text.strip()
                    article_dict['link'] = link 
                    article_dict['date'] = self.convert_to_valid_datetime(post_date.text.strip())
                    article_dict['source'] = config['source']
                    last_date = post_date.text.strip()
                else:
                    article_dict = {}
                    article_dict['title'] = post_title.text.strip()
                    article_dict['link'] = link 
                    article_dict['date'] = self.convert_to_valid_datetime(last_date) if len(last_date) > 0 else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    article_dict['source'] = config['source']

                result.append(article_dict)
                    
        
        return result
    
    def convert_to_valid_datetime(self, date_str):
        try: 
            date_obj = parser.parse(date_str)
            return date_obj
        except Exception as err:
            print('Error occured while validating datetime ', err)
            raise ValueError("Invalid date type ", date_str)
    
    def news_db_insertion(self, records):
        insert_query = """
                INSERT INTO NewsTracker (title, date, link, source)
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM NewsTracker AS n
                    WHERE n.title = ? AND n.link = ? AND n.date = ?
                );
            """
        data = [(record['title'], record['date'], record['link'], record['source'],record['title'], record['link'], record['date']) for record in records]
        return self.db_manager.multiple_inserts(insert_query, data)

    def get_market_map_from_page_ngx(self, soup:BeautifulSoup):
        change = soup.find(class_='d-dquote-x1-5')
        marketCap = soup.find(class_='table table-hover table-striped wpDataTable')
        if marketCap:
            capValue = marketCap.find(class_='MarketCap')
            if capValue:
                marketCapValue = capValue.text

        if change:
            start_index = change.text.find('(') + 1
            end_index = change.text.find(')')
            changeValue = change.text[start_index:end_index].strip()

        print(changeValue)
        print(marketCapValue)
        #print(marketCap)

    def crawl_news(self):
        self.config = self._get_config()
        articles = []
        for config in self.config:
            config = json.loads(config)
            soup = self.download_page(config['url'])
            result = self.process_news(soup, config)
            articles.extend(result)
        print('found {0} articles'.format(len(articles)))
        print('doing an insertion')
        distinct_articles = {x['title']:x for x in articles}.values()
        res = self.news_db_insertion(distinct_articles)
        print('insertion completed with code {0}'.format(res))
    
    def crawl_news_test(self, config):
        self.config = self._get_config()
        articles = []
        soup = self.download_page(config['url'])
        result = self.process_news(soup, config)
        articles.extend(result)
        print(articles)
    
    def market_map_test(self):
        url = 'https://ngxgroup.com/exchange/data/company-profile/?isin=NGACCESS0005&directory=companydirectory'
        soup = self.download_page(url)
        self.get_market_map_from_page_ngx(soup)
    
    def verify_webpage(self):
        pages_to_verify = self.db_manager.fetch_records("select * from companies", ())
        print(pages_to_verify)
        for page in pages_to_verify:
            link = page[-1]
            #print('trying page {0}'.format(link))
            res = requests.get(link)
            if res.status_code != 200: 
                print('page {0} does not exists status {1}'.format(link, res.status_code))
            
            #time.sleep(5)
    
    def get_markets_from_afx(self):
        afx_configs = [{
            'url': 'https://afx.kwayisi.org/ngx/',
            'market': 'ngx'
        }]
        with open('output_afx.csv', mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for afx_config in afx_configs:
                soup = self.download_page(afx_config['url'])
                table_class = soup.find(class_='t')
                table = table_class.find('table')
                tr = table.find('tr')
                tr_arr = tr.decode_contents().split('<tr>')
                for tr in tr_arr:
                    fixed_tr = tr.replace('<td>', '</td><td>')
                    soup_tr = BeautifulSoup(fixed_tr, 'html.parser')
                    tds = soup_tr.find_all('td')
                    cols = []

                    cols.append(afx_config['market'])
                    foundLink = False
                    for td in tds:
                        if td:
                            cols.append(td.text.strip())
                        link = td.find('a')
                        if link and foundLink==False:
                            cols.append(link.get('href'))
                            foundLink = True
                    #format 2nd to last column
                    if len(cols) >= 2:
                        val2 = cols[-2]
                        if '-' in val2:
                            cols[-2] = val2.split('-')[0]
                        if '+' in val2:
                            cols[-2] = val2.split('+')[0]
                    writer.writerow(cols)

            


if __name__ == "__main__":
    db_manager = DatabaseManager(
        server=os.getenv('DB_SERVER'),
        database=os.getenv('DB_NAME'),
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS')
    )
    crawler = Crawl(db_manager)
    crawler.market_map_test()
    # crawler.market_map_test()




