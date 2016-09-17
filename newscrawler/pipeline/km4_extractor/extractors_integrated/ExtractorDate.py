from src.extractors_integrated.ArticleDateExtractor import *
from src.extractors_integrated.ExtractorInterface import *


class DateExtractor(ExtractorInterface):
    """This class implements ArticleDateExtractor as an article extractor. ArticleDateExtractor is
    a subclass of Extractor.

    :param html: A string, the html document
    """

    document = None

    def __init__(self, html):
        self.html = html

    def name(self):
        """Returns the name of the article extractor."""
        name = "date_extractor"
        return name

    def language(self):
        """ArticleDateExtractor can't extract the language."""
        return None

    def title(self):
        """ArticleDateExtractor can't extract the title."""
        return None

    def description(self):
        """ArticleDateExtractor cant't extract the description."""
        return None

    def text(self):
        """ArticleDateExtractor can't extract the maintext."""
        return None

    def topimage(self):
        """ArticleDateExtractor can't extract the topimage."""
        return None

    def author(self):
        """ArticleDateExtractor cant't extract the author."""
        return None

    def publish_date(self):
        """Returns the publish_date of the extracted article."""
        publish_date = extractArticlePublishedDate("", self.html)
        return publish_date
