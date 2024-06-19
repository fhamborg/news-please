import logging

import scrapy

from newsplease.crawler.spiders.newsplease_spider import NewspleaseSpider


class Download(NewspleaseSpider, scrapy.Spider):
    name = "Download"
    start_urls = None

    log = None

    config = None
    helper = None

    def __init__(self, helper, url, config, ignore_regex, *args, **kwargs):
        self.log = logging.getLogger(__name__)

        self.config = config
        self.helper = helper

        if isinstance(url, list):
            self.start_urls = url
        else:
            self.start_urls = [url]

        super(Download, self).__init__(*args, **kwargs)

    def parse(self, response):
        """
        Passes the response to the pipeline.

        :param obj response: The scrapy response
        """
        if not self.helper.parse_crawler.content_type(response):
            return

        yield self.helper.parse_crawler.pass_to_pipeline(
            response,
            self.helper.url_extractor.get_allowed_domain(response.url)
        )

    @staticmethod
    def supports_site(url):
        """
        As long as the url exists, this crawler will work!

        Determines if this crawler works on the given url.

        :param str url: The url to test
        :return bool: Determines wether this crawler work on the given url
        """
        return True
