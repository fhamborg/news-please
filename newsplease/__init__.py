import sys
import urllib

import os

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from newsplease.pipeline.extractor import article_extractor
from newsplease.crawler.items import NewscrawlerItem
from dotmap import DotMap
from newsplease.pipeline.pipelines import ExtractedInformationStorage
from newsplease.crawler.simple_crawler import SimpleCrawler


class NewsPlease:
    """
    Access news-please functionality via this interface
    """

    @staticmethod
    def from_warc(warc_record):
        """
        Extracts relevant information from a WARC record. This function does not invoke scrapy but only uses the article
        extractor.
        :return:
        """
        html = str(warc_record.raw_stream.read())
        url = warc_record.rec_headers.get_header('WARC-Target-URI')
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

        # if an url was given, we can use that as the filename
        filename = urllib.parse.quote_plus(url) + '.json'

        item = NewscrawlerItem()
        item['spider_response'] = DotMap()
        item['spider_response'].body = html
        item['url'] = url
        item['source_domain'] = urlparse(url).hostname.encode() if url != '' else ''.encode()
        item['html_title'] = title_encoded
        item['rss_title'] = title_encoded
        item['local_path'] = None
        item['filename'] = filename
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
        results = {}

        if len(urls) == 0:
            pass
        elif len(urls) == 1:
            url = urls[0]
            html = SimpleCrawler.fetch_url(url)
            results[url] = NewsPlease.from_html(html, url)
        else:
            results = SimpleCrawler.fetch_urls(urls)
            for url in results:
                results[url] = NewsPlease.from_html(results[url], url)

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
        NewsPlease.__is_crawler_closed = True


if __name__ == '__main__':
    articles = NewsPlease.from_urls([
        'https://www.nytimes.com/2017/06/27/us/politics/mitch-mcconnell-health-care-repeal.html?&hp&action=click&pgtype=Homepage&clickSource=story-heading&module=first-column-region&region=top-news&WT.nav=top-news&_r=0',
        'https://www.washingtonpost.com/powerpost/mcconnell-is-known-as-a-deal-closer-but-hes-never-done-policy-this-big/2017/06/28/df7a0810-5b76-11e7-a9f6-7c3296387341_story.html?hpid=hp_hp-top-table-main_pkcapitol-10am%3Ahomepage%2Fstory',
        'felix.fadljh'
    ])

    for url in articles:
        article = articles[url]
        print(article.title)
