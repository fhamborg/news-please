"""
This file's only purpose is to bundle all helper classes in ./helper_classes
so they can be passed to other classes easily
"""

from .helper_classes.heuristics import Heuristics
from .helper_classes.parse_crawler import ParseCrawler
from .helper_classes.savepath_parser import SavepathParser
from .helper_classes.url_extractor import UrlExtractor


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
            crawler_class,
            crawler_item_class,
            working_path
    ):
        if not isinstance(sites_object[0]["url"], list):
            self.heuristics = Heuristics(
                cfg_heuristics, sites_object, crawler_class)
        self.url_extractor = UrlExtractor()
        self.savepath_parser = SavepathParser(
            cfg_savepath, relative_to_path, format_relative_path, self, working_path)
        self.crawler_item_class = crawler_item_class
        self.parse_crawler = ParseCrawler(self)
