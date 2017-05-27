import sys

import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from newsplease.pipeline.pipelines import InMemoryStorage
from newsplease.single_crawler import SingleCrawler
import time
from scrapy import signals
from pydispatch import dispatcher

import pathlib
import uuid
import os


class NewsPlease:
    """
    Access news-please functionality via this interface
    """
    is_crawler_closed = False

    @staticmethod
    def from_text(text):
        tmp_filename = os.path.realpath(uuid.uuid4().hex)

        with open(tmp_filename, 'w') as tmp_file:
            tmp_file.write(text)
            try:
                tmp_article = NewsPlease.from_url(pathlib.Path(tmp_filename).as_uri())
                if tmp_article:
                    print(tmp_article['title'])
            except:
                pass

        os.remove(tmp_filename)

    @staticmethod
    def from_url(url):
        """
        Crawls the article from the url and extracts relevant information.
        :param url:
        :return: A dict containing all the information of the article. Else, None.
        """
        articles = NewsPlease.from_urls([url])
        if url in articles.keys():
            return articles[url]
        else:
            return None

    @staticmethod
    def from_urls(urls):
        """
        Crawls articles from the urls and extracts relevant information.
        :param urls:
        :return: A dict containing given URLs as keys, and extracted information as corresponding values.
        """
        SingleCrawler.create_as_library(urls)
        dispatcher.connect(NewsPlease.__spider_closed, signals.spider_closed)

        # wait for the crawler to close
        while not NewsPlease.is_crawler_closed:
            time.sleep(0.01)

        # the crawler has completed, we need to get the results
        results = InMemoryStorage.get_results()
        NewsPlease.is_crawler_closed = False
        return results

    @staticmethod
    def from_file(path):
        """
        Crawls articles from the urls and extracts relevant information.
        :param path: path to file containing urls (each line contains one URL)
        :return: A dict containing given URLs as keys, and extracted information as corresponding values.
        """
        with open(path) as f:
            content = f.readlines()
        content = [x.strip() for x in content]
        urls = list(filter(None, content))

        return NewsPlease.from_urls(urls)

    @staticmethod
    def __spider_closed(spider, reason):
        NewsPlease.is_crawler_closed = True


if __name__ == "__main__":
    NewsPlease.from_text('<html></html>')
