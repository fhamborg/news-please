import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from newsplease.pipeline.pipelines import InMemoryStorage
from newsplease.single_crawler import SingleCrawler


class NewsPleaseLib:
    """
    Access news-please functionality via this interface
    """

    @staticmethod
    def download_article(url):
        """
        Crawls the article from the url and extracts relevant information.
        :param url:
        :return:
        """
        SingleCrawler.create_as_library(url)
        results = InMemoryStorage.get_results()
        article = results[url]
        del results[url]
        return article

    @staticmethod
    def download_articles(urls):
        """
        Crawls articles from the urls and extracts relevant information.
        :param urls:
        :return:
        """
        SingleCrawler.create_as_library(urls)
        results = InMemoryStorage.get_results()
        articles = []
        for url in urls:
            article = results[url]
            del results[url]
            articles.append(article)
            print(article['title'])
        return articles

if __name__ == '__main__':
    NewsPleaseLib.download_article('http://www.zeit.de/politik/deutschland/2017-02/fluechtlinge-asylverfahren-bamf-taeuschung-afghanistan')