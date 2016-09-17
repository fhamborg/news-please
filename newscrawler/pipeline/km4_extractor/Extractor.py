from src.extractors_integrated.ExtractorDate import *
from src.extractors_integrated.ExtractorNewspaper import Newspaper
from src.extractors_integrated.ExtractorReadability import Readability
from src.extractors_integrated.ExtractorLangDetect import LangDetect
from src.help_classes.ArticleCandidate import *
from src.IO_handler.ConfigHandler import *


class Extractor:
    """This class initializes all extractors and saves the results of them. When adding a new extractor, it needs to
    be initialized here and added to list_extractor.
    """

    def __init__(self):
        self.config_handler = ConfigHandler()

    def str_to_class(self, extractor_object):
        return getattr(self, extractor_object)

    def extract(self, article_raw):
        """Initialize every extractor and pass the raw article.

        :param article_raw: An ArticleRaw-Object, the raw article from the database
        :return: A list, the extracted ArticleCandidate-Objects (One for each extractor)
        """

        self.newspaper = Newspaper(article_raw.html)
        self.readability = Readability(article_raw.html)
        self.date_extractor = DateExtractor(article_raw.html)
        self.lang_detect = LangDetect(article_raw.page_title)
        list_extractor = []
        path = dirname(__file__)
        # Add extractor to list
        if isinstance(self.config_handler.extractors, str):
            list_extractor.append(self.str_to_class(self.config_handler.extractors))
        else:
            for x in self.config_handler.extractors:
                list_extractor.append(self.str_to_class(x))

        list_article_candidate = []

        for extractor in list_extractor:
            article_candidate = ArticleCandidate()
            article_candidate.title = extractor.title()
            article_candidate.description = extractor.description()
            article_candidate.text = extractor.text()
            article_candidate.topimage = extractor.topimage()
            article_candidate.author = extractor.author()
            article_candidate.publish_date = extractor.publish_date()
            article_candidate.extractor = extractor.name()
            article_candidate.language = extractor.language()
            article_candidate.url = article_raw.url

            list_article_candidate.append(article_candidate)

        return list_article_candidate