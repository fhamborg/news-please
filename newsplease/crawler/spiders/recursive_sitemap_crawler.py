import logging

import scrapy


from newsplease.crawler.spiders.newsplease_spider import NewspleaseSpider
from newsplease.helper_classes.url_extractor import UrlExtractor


class RecursiveSitemapCrawler(NewspleaseSpider, scrapy.spiders.SitemapSpider):
    name = "RecursiveSitemapCrawler"
    allowed_domains = None
    sitemap_urls = None
    original_url = None

    log = None

    config = None
    helper = None

    ignore_regex = None
    ignore_file_extensions = None

    def __init__(self, helper, url, config, ignore_regex, *args, **kwargs):
        self.log = logging.getLogger(__name__)

        self.config = config
        self.helper = helper

        self.ignore_regex = ignore_regex
        self.ignore_file_extensions = self.config.section("Crawler")[
            "ignore_file_extensions"
        ]

        self.original_url = url

        self.allowed_domains = [self.helper.url_extractor.get_allowed_domain(url)]
        self.check_certificate = (bool(config.section("Crawler").get('check_certificate'))
                                  if config.section("Crawler").get('check_certificate') is not None
                                  else True)
        self.sitemap_urls = self.helper.url_extractor.get_sitemap_urls(
            domain_url=url,
            allow_subdomains=config.section("Crawler")["sitemap_allow_subdomains"],
            check_certificate=self.check_certificate,
        )
        super(RecursiveSitemapCrawler, self).__init__(*args, **kwargs)

    def parse(self, response):
        """
        Checks any given response on being an article and if positiv,
        passes the response to the pipeline.

        :param obj response: The scrapy response
        """
        if not self.helper.parse_crawler.content_type(response):
            return

        for request in self.helper.parse_crawler.recursive_requests(
            response, self, self.ignore_regex, self.ignore_file_extensions
        ):
            yield request

        yield self.helper.parse_crawler.pass_to_pipeline_if_article(
            response, self.allowed_domains[0], self.original_url
        )

    @staticmethod
    def supports_site(url: str, check_certificate: bool = True) -> bool:
        """
        Sitemap-Crawler are supported by every site which have a
        Sitemap set in the robots.txt.

        Determines if this crawler works on the given url.

        :param str url: The url to test
        :param bool check_certificate:
        :return bool: Determines wether this crawler work on the given url
        """
        return UrlExtractor.sitemap_check(url=url, check_certificate=check_certificate)
