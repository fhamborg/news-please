"""
This file's only purpose is to bundle all helper classes in ./helper_classes
so they can be passed to other classes easily
"""

from newscrawler.helper_classes.heuristics import Heuristics
from newscrawler.helper_classes.url_extractor import UrlExtractor
from newscrawler.helper_classes.savepath_parser import SavepathParser
from newscrawler.helper_classes.parse_crawler import ParseCrawler


class Helper(object):
    """
    This class contains helper classes from ./helper_classes.
    """
    heuristics = None
    url_extractor = None
    savepath_parser = None
    parse_crawler = None

    def __init__(
            self,
            cfg_heuristics,
            cfg_savepath,
            relative_to_path,
            format_relative_path,
            sites_object,
            crawler_class
    ):
        if not isinstance(sites_object[0]["url"], list):
            self.heuristics = Heuristics(
                cfg_heuristics, sites_object, crawler_class)
        self.url_extractor = UrlExtractor()
        self.savepath_parser = SavepathParser(
            cfg_savepath, relative_to_path, format_relative_path, self)
        self.parse_crawler = ParseCrawler(self)
