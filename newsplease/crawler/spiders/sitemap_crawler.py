import logging

import scrapy


from newsplease.crawler.spiders.newsplease_spider import NewspleaseSpider
from newsplease.helper_classes.url_extractor import UrlExtractor


class SitemapCrawler(NewspleaseSpider, scrapy.spiders.SitemapSpider):
    name = "SitemapCrawler"
    allowed_domains = None
    sitemap_urls = None
    original_url = None

    log = None

    config = None
    helper = None

    def __init__(self, helper, url, config, ignore_regex, *args, **kwargs):
        self.log = logging.getLogger(__name__)

        self.config = config
        self.helper = helper
        self.original_url = url

        self.allowed_domains = [
            self.helper.url_extractor.get_allowed_domain(
                url, config.section("Crawler")["sitemap_allow_subdomains"]
            )
        ]
        self.sitemap_urls = self.helper.url_extractor.get_sitemap_urls(
            url, config.section("Crawler")["sitemap_allow_subdomains"]
        )

        self.log.debug(self.sitemap_urls)

        super(SitemapCrawler, self).__init__(*args, **kwargs)

    def parse(self, response):
        """
        Checks any given response on being an article and if positiv,
        passes the response to the pipeline.

        :param obj response: The scrapy response
        """
        if not self.helper.parse_crawler.content_type(response):
            return

        yield self.helper.parse_crawler.pass_to_pipeline_if_article(
            response, self.allowed_domains[0], self.original_url
        )

    @staticmethod
    def only_extracts_articles():
        """
        Meta-Method, so if the heuristic "crawler_contains_only_article_alikes"
        is called, the heuristic will return True on this crawler.
        """
        return True

    @staticmethod
    def supports_site(url):
        """
        Sitemap-Crawler are supported by every site which have a
        Sitemap set in the robots.txt.

        Determines if this crawler works on the given url.

        :param str url: The url to test
        :return bool: Determines wether this crawler work on the given url
        """

        return UrlExtractor.sitemap_check(url)
