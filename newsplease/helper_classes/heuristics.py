"""
Helper class for testing heuristics
"""
import re

from .sub_classes.heuristics_manager import HeuristicsManager
from .url_extractor import UrlExtractor


class Heuristics(HeuristicsManager):
    """
    Helper class for testing heuristics
    """

    def crawler_contains_only_article_alikes(self, response, site_dict):
        """
        Some crawlers (rssCrawlers, sitemapCrawlers) only return sites, which
        are actually articles or article-collections.
        This heuristic, checks which crawler is used and if one of those
        crawlers is used, it returns true.

        :param obj response: The scrapy response
        :param dict site_dict: The site object from the JSON-File

        :return bool: true if it is a crawler which only returns articles or
                      article-collections
        """
        try:
            return self.crawler_class.only_extracts_articles()
        except AttributeError:
            return False

    def meta_contains_article_keyword(self, response, site_dict):
        """
        Determines wether the response's meta data contains the keyword
        'article'

        :param obj response: The scrapy response
        :param dict site_dict: The site object from the JSON-File

        :return bool: Determines wether the reponse's meta data contains the
                      keyword 'article'
        """
        contains_meta = response.xpath('//meta') \
            .re('(= ?["\'][^"\']*article[^"\']*["\'])')

        if not contains_meta:
            return False
        return True

    @staticmethod
    def og_type(response, site_dict):
        """
        Check if the site contains a meta-tag which contains
        property="og:type" and content="article"

        :param obj response: The scrapy response
        :param dict site_dict: The site object from the JSON-File

        :return bool: True if the tag is contained.
        """
        og_type_article = response.xpath('//meta') \
            .re('(property=["\']og:type["\'].*content=["\']article["\'])|'
                '(content=["\']article["\'].*property=["\']og:type["\'])')
        if not og_type_article:
            return False

        return True

    def linked_headlines(self, response, site_dict, check_self=False):
        """
        Checks how many of the headlines on the site contain links.

        :param obj response: The scrapy response
        :param dict site_dict: The site object from the JSON-File
        :param bool check_self: Check headlines/
                                headlines_containing_link_to_same_domain
                                instead of headline/headline_containing_link

        :return float: ratio headlines/headlines_containing_link
        """
        h_all = 0
        h_linked = 0
        domain = UrlExtractor.get_allowed_domain(site_dict["url"], False)

        # This regex checks, if a link containing site_domain as domain
        # is contained in a string.
        site_regex = r"href=[\"'][^\/]*\/\/(?:[^\"']*\.|)%s[\"'\/]" % domain
        for i in range(1, 7):
            for headline in response.xpath('//h%s' % i).extract():
                h_all += 1
                if "href" in headline and (
                            not check_self or re.search(site_regex, headline)
                        is not None):
                    h_linked += 1

        self.log.debug("Linked headlines test: headlines = %s, linked = %s",
                       h_all, h_linked)

        min_headlines = self.cfg_heuristics["min_headlines_for_linked_test"]
        if min_headlines > h_all:
            self.log.debug("Linked headlines test: Not enough headlines "
                           "(%s < %s): Passing!", h_all, min_headlines)
            return True

        return float(h_linked) / float(h_all)

    def self_linked_headlines(self, response, site_dict):
        """
        Checks how many of the headlines on the site contain links.

        :param obj response: The scrapy response
        :param dict site_dict: The site object from the JSON-File

        :return float: ratio headlines/headlines_containing_link_to_same_domain
        """
        return self.linked_headlines(response, site_dict, True)

    def is_not_from_subdomain(self, response, site_dict):
        """
        Ensures the response's url isn't from a subdomain.

        :param obj response: The scrapy response
        :param dict site_dict: The site object from the JSON-File

        :return bool: Determines if the response's url is from a subdomain
        """

        root_url = re.sub(r'https?://[a-z]+.', '', site_dict["url"])
        return UrlExtractor.get_allowed_domain(response.url) == root_url
