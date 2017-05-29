import sys

import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from newsplease.pipeline.pipelines import InMemoryStorage
from newsplease.single_crawler import SingleCrawler
import time
from scrapy import signals
from pydispatch import dispatcher
from newsplease.pipeline.extractor import article_extractor
from newsplease.crawler.items import NewscrawlerItem
from dotmap import DotMap
from newsplease.pipeline.pipelines import ExtractedInformationStorage
from urllib.parse import urlparse


class NewsPlease:
    """
    Access news-please functionality via this interface
    """
    is_crawler_closed = False

    @staticmethod
    def from_warc(warc_record):
        """
        Extracts relevant information from a WARC record. This function does not invoke scrapy but only uses the article
        extractor.
        :return:
        """
        html = str(warc_record.payload.read())
        url = warc_record.url
        article = NewsPlease.from_html(html, url)
        return article

    @staticmethod
    def from_html(html, url=None):
        """
        Extracts relevant information from an HTML page given as a string. This function does not invoke scrapy but only
        uses the article extractor.
        :param html:
        :param url:
        :return:
        """
        extractor = article_extractor.Extractor(
            ['newspaper_extractor', 'readability_extractor', 'date_extractor', 'lang_detect_extractor'])

        title_encoded = ''.encode()
        if not url:
            url = ''

        item = NewscrawlerItem()
        item['spider_response'] = DotMap()
        item['spider_response'].body = html
        item['url'] = url
        item['source_domain'] = urlparse(url).hostname.encode() if url != '' else ''.encode()
        item['html_title'] = title_encoded
        item['rss_title'] = title_encoded
        item['local_path'] = None
        item['filename'] = None
        item['download_date'] = None
        item['modified_date'] = None
        item = extractor.extract(item)

        article = ExtractedInformationStorage.extract_relevant_info(item)
        return DotMap(article)

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

        # convert to DotMap
        for url in results:
            results[url] = DotMap(results[url])

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
