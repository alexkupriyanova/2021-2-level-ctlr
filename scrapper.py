"""
Scrapper implementation
"""
from datetime import datetime
from pathlib import Path
import json
import shutil
from time import sleep

from bs4 import BeautifulSoup
import requests

from core_utils.article import Article
from constants import ASSETS_PATH, CRAWLER_CONFIG_PATH, HTTP_PATTERN

class IncorrectURLError(Exception):
    """
    Seed URL does not match standard pattern
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Total number of articles to parse is too big
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Total number of articles to parse in not integer
    """


class Crawler:
    """
    Crawler implementation
    """
    def __init__(self, seed_urls, max_articles: int):
        self.seed_urls = seed_urls
        self.max_articles = max_articles
        self.urls = []


    def _extract_url(self, article_bs):
        not_full_urls = []
        all_urls_bs = article_bs.find_all('a')
        for url_bs in all_urls_bs:
            url_to_article = url_bs['href']
            not_full_urls.append(url_to_article)
        full_urls = [HTTP_PATTERN + not_full_url for not_full_url in
                     not_full_urls if not 'http' in not_full_url]

        for full_url in full_urls:
            if len(self.urls) < self.max_articles and full_url not in self.urls:
                self.urls.append(full_url)

    def find_articles(self):
        """
        Finds articles
        """
        for seed_url in self.seed_urls:
            sleep (3)
            response = requests.get(url=seed_url, timeout=60)
            if not response.ok:
                continue
            soup = BeautifulSoup (response.text, 'lxml')
            self._extract_url(soup)


    def get_search_urls(self):
        """
        Returns seed_urls param
        """
        return self.seed_urls

class HTMLParser:
    def __init__(self, article_url, article_id):
        self.article_url = article_url
        self.article_id = article_id
        self.article = Article(self.article_url, self.article_id)

    def _fill_article_with_meta_information(self, article_bs):

        self.article.title = article_bs.find('h2', class_= 'mname').text.strip()

        try:
            self.article.author = article_bs.find('p', 'font size="3"', 'strong', 'em').text.strip().split('  ')[0]
        except AttributeError:
            self.article.author = 'NOT FOUND'

        self.article.topics.append(article_bs.find('p', 'strong', 'font size="3"').text)

        raw_date = article_bs.find('div', class_='mndata').find('time')['datetime'][:-5]
        self.article.date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S')

    def _fill_article_with_text(self, article_bs):
        self.article.text = ''
        texts_bs = article_bs.find('div', class_='onemidnew')
        list_with_texts = texts_bs.find_all('p')
        for text_bs in list_with_texts:
            self.article.text += text_bs.text

    def parse(self):
        response = requests.get(url=self.article_url, timeout=60)
        article_bs = BeautifulSoup(response.text, 'lxml')
        self._fill_article_with_text(article_bs)
        self._fill_article_with_meta_information(article_bs)

        return self.article


def prepare_environment(base_path):
    """
    Creates ASSETS_PATH folder if not created and removes existing folder
    """
    main_path = Path(base_path)
    if main_path.exists():
        shutil.rmtree(base_path)
    main_path.mkdir(parents = True)

def validate_config(crawler_path):
    """
    Validates given config
    """
    with open(crawler_path) as file:
        configuration = json.load(file)

    if not configuration ['seed_urls']:
        raise IncorrectURLError

    for url in configuration["seed_urls"]:
        if HTTP_PATTERN not in url:
            raise IncorrectURLError

    seed_urls = configuration["seed_urls"]
    total_articles_to_find_and_parse = configuration["total_articles_to_find_and_parse"]

    if not isinstance(total_articles_to_find_and_parse, int) or total_articles_to_find_and_parse <= 0:
        raise IncorrectNumberOfArticlesError

    if total_articles_to_find_and_parse > 200:
        raise NumberOfArticlesOutOfRangeError

    return seed_urls, total_articles_to_find_and_parse


if __name__ == '__main__':
    seed_urls_main, total_articles_main = validate_config(CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)

    crawler = Crawler(seed_urls_main, total_articles_main)
    crawler.find_articles()

    COUNTER_ID = 1
    for article_url_main in crawler.urls:
        article_parser = HTMLParser(article_url = article_url_main, article_id = COUNTER_ID)
        article = article_parser.parse()
        article.save_raw()
        COUNTER_ID += 1
