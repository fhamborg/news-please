from requests import get
from scrapy.http import TextResponse, XmlResponse

from newsplease.crawler.spiders.newsplease_spider import NewspleaseSpider
from newsplease.helper_classes.url_extractor import UrlExtractor

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
import logging
import re

import scrapy

# to improve performance, regex statements are compiled only once per module
re_rss = re.compile(
    r'(<link[^>]*href[^>]*type ?= ?"application\/rss\+xml"|' +
    r'<link[^>]*type ?= ?"application\/rss\+xml"[^>]*href)'
)


class RssCrawler(NewspleaseSpider, scrapy.Spider):
    name = "RssCrawler"
    ignored_allowed_domains = None
    start_urls = None
    original_url = None

    log = None

    config = None
    helper = None

    def __init__(self, helper, url, config, ignore_regex, *args, **kwargs):
        self.log = logging.getLogger(__name__)

        self.config = config
        self.helper = helper

        self.original_url = url

        self.ignored_allowed_domain = self.helper.url_extractor \
            .get_allowed_domain(url)
        self.start_urls = [self.helper.url_extractor.get_start_url(url)]

        super(RssCrawler, self).__init__(*args, **kwargs)

    def parse(self, response):
        """
        Extracts the Rss Feed and initiates crawling it.

        :param obj response: The scrapy response
        """
        yield scrapy.Request(
            UrlExtractor.get_rss_url(response), callback=self.rss_parse
        )

    def rss_parse(self, response):
        """
        Extracts all article links and initiates crawling them.

        :param obj response: The scrapy response
        """
        for item in response.xpath('//item'):
            for url in item.xpath('link/text()').extract():
                yield scrapy.Request(url, lambda resp: self.article_parse(
                    resp, item.xpath('title/text()').extract()[0]))

    def article_parse(self, response, rss_title=None):
        """
        Checks any given response on being an article and if positiv,
        passes the response to the pipeline.

        :param obj response: The scrapy response
        :param str rss_title: Title extracted from the rss feed
        """
        if not self.helper.parse_crawler.content_type(response):
            return

        yield self.helper.parse_crawler.pass_to_pipeline_if_article(
            response, self.ignored_allowed_domain, self.original_url,
            rss_title)

    @staticmethod
    def only_extracts_articles():
        """
        Meta-Method, so if the heuristic "crawler_contains_only_article_alikes"
        is called, the heuristic will return True on this crawler.
        """
        return True

    @staticmethod
    def get_potential_redirection_from_url(url):
        """Ensure we have the correct URL to check for RSS feed"""
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
        url = UrlExtractor.url_to_request_with_agent(url)
        redirect_url = opener.open(url).url
        return redirect_url

    @staticmethod
    def supports_site(url):
        """
        Rss Crawler are supported if by every site containing an rss feed.

        Determines if this crawler works on the given url.

        :param str url: The url to test
        :return bool: Determines wether this crawler work on the given url
        """

        # Follow redirects
        redirect_url = RssCrawler.get_potential_redirection_from_url(url)
        redirect = UrlExtractor.url_to_request_with_agent(redirect_url)

        # Check if a standard rss feed exists
        response = urllib2.urlopen(redirect).read()
        return re.search(re_rss, response.decode("utf-8")) is not None

    @staticmethod
    def has_urls_to_scan(url: str) -> bool:
        """
        Check if the RSS feed contains any URL to scan

        :param str url: The url to test
        :return bool:
        """
        redirect_url = RssCrawler.get_potential_redirection_from_url(url)

        response = get(redirect_url)
        scrapy_response = TextResponse(url=redirect_url, body=response.text.encode())

        rss_url = UrlExtractor.get_rss_url(scrapy_response)
        rss_content = get(rss_url).text
        rss_response = XmlResponse(url=rss_url, body=rss_content, encoding="utf-8")

        urls_to_scan = [
            url
            for item in rss_response.xpath("//item")
            for url in item.xpath("link/text()").extract()
        ]

        return len(urls_to_scan) > 0
