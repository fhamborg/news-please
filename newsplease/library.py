from newsplease.single_crawler import SingleCrawler
import os


class Library:
    """
    Access news-please functionality via this interface
    """
    crawler = None

    def __init__(self):
        url = 'https://www.nytimes.com/2017/02/22/us/politics/devos-sessions-transgender-students-rights.html'
        SingleCrawler.create_as_library(url)

    def download_article(self, url):
        """
        Crawls the article from the url and extracts relevant information.
        :param url:
        :return:
        """
        # self.crawler.library_download_urls([url])
        pass

    def download_articles(self, urls):
        """
        Crawls articles from the urls and extracts relevant information.
        :param urls:
        :return:
        """
        articles = []
        for url in urls:
            articles.append(self.downloadArticle(url))
        return articles


if __name__ == '__main__':
    lib = Library()
    lib.download_article(
        'https://www.nytimes.com/2017/02/22/us/politics/devos-sessions-transgender-students-rights.html')
    print("hi")
    lib.download_article(
        'http://www.faz.net/aktuell/gesellschaft/kenia-droht-hungerkatastrophe-wegen-el-ni-o-14890707.html')