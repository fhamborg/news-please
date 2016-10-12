from newscrawler.pipeline.km4_extractor.extractors.abstract_extractor import *
from langdetect import detect


class Extractor(AbstractExtractor):
    """This class implements LangDetect as an article extractor but it can only
    detect the extracted language (en, de, ...).

    """

    def __init__(self):
        self.name = "langdetect"

    def _language(self, item):
        """Returns the language of the extracted article using the pageTitle or RSS title"""
        if item['html_title'] is not None:
            return detect(item['html_title'].decode("utf-8"))
        if item['rss_title'] is not None:
            return detect(item['rss_title'])
        return None
