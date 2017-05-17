import sys

import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from newsplease.pipeline.pipelines import InMemoryStorage
from newsplease.single_crawler import SingleCrawler
import time
from scrapy import signals
from pydispatch import dispatcher


class NewsPlease:
    """
    Access news-please functionality via this interface
    """
    is_crawler_closed = False

    @staticmethod
    def download_article(url):
        """
        Crawls the article from the url and extracts relevant information.
        :param url:
        :return: A dict containing all the information of the article.
        """
        return NewsPlease.download_articles([url])[url]

    @staticmethod
    def download_articles(urls):
        """
        Crawls articles from the urls and extracts relevant information.
        :param urls:
        :return: A dict containing given URLs as keys, and extracted information as corresponding values.
        """
        SingleCrawler.create_as_library(urls)
        dispatcher.connect(NewsPlease.spider_closed, signals.spider_closed)

        # wait for the crawler to close
        while not NewsPlease.is_crawler_closed:
            time.sleep(0.01)

        # the crawler has completed, we need to get the results
        results = InMemoryStorage.get_results()
        NewsPlease.is_crawler_closed = False
        return results

    @staticmethod
    def download_from_file(path):
        """
        Crawls articles from the urls and extracts relevant information.
        :param path: path to file containing urls (each line contains one URL)
        :return: A dict containing given URLs as keys, and extracted information as corresponding values.
        """
        with open(path) as f:
            content = f.readlines()
        content = [x.strip() for x in content]
        urls = list(filter(None, content))

        return NewsPlease.download_articles(urls)

    @staticmethod
    def spider_closed(spider, reason):
        NewsPlease.is_crawler_closed = True
