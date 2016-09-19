from newscrawler.pipeline.km4_extractor.extractors.ExtractorInterface import *
from langdetect import detect


class LangDetect(ExtractorInterface):
    """This class implements LangDetect as an article extractor but it can only
    detect the extracted language (en, de, ...).

    """

    def _name(self):
        """Returns the name of the article extractor."""
        return "langdetect"

    def _language(self, item):
        """Returns the language of the extracted article using the pageTitle or RSS title"""
        if item['html_title'] is not None:
            return detect(item['html_title'])
        if item['rss_title'] is not None:
            return detect(item['rss_title'])
        return None
