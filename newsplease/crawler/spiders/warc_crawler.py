import logging

import scrapy
import warc


class DummyMdw(object):
    def process_request(self, request, spider):
        record = request.meta['record']
        payload = record.payload.read()
        headers, body = payload.split('\r\n\r\n', 1)
        url = record['WARC-Target-URI']
        return scrapy.Response(url=url, status=200, body=body, headers=headers)


class WarcCrawler(scrapy.spiders.Spider):
    name = "WarcCrawler"
    allowed_domains = None
    sitemap_urls = None
    original_url = None

    log = None

    config = None
    helper = None

    ignore_regex = None
    ignore_file_extensions = None

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {'x.DummyMdw': 1}
    }

    def __init__(self, helper, url, config, ignore_regex, *args, **kwargs):
        self.log = logging.getLogger(__name__)

        self.config = config
        self.helper = helper

        self.ignore_regex = ignore_regex
        self.ignore_file_extensions = self.config.section(
            'Crawler')['ignore_file_extensions']

        self.original_url = url

        self.allowed_domains = [self.helper.url_extractor
                                    .get_allowed_domain(url)]
        self.sitemap_urls = [self.helper.url_extractor.get_sitemap_url(
            url, config.section('Crawler')['sitemap_allow_subdomains'])]

    def start_requests(self):
        f = warc.WARCFile(fileobj=gzip.open("file.war.gz"))
        for record in f:
            if record.type == "response":
                yield scrapy.Request(url, callback=self.parse, meta={'record': record})

    def parse(self, response):
        """
        Checks any given response on being an article and if positiv,
        passes the response to the pipeline.

        :param obj response: The scrapy response
        """
        if not self.helper.parse_crawler.content_type(response):
            return

        for request in self.helper.parse_crawler \
                .recursive_requests(response, self, self.ignore_regex,
                                    self.ignore_file_extensions):
            yield request

        yield self.helper.parse_crawler.pass_to_pipeline_if_article(
            response, self.allowed_domains[0], self.original_url)

    @staticmethod
    def supports_site(url):
        return True
