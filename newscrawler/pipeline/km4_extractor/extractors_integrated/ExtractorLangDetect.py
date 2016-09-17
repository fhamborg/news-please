from src.extractors_integrated.ExtractorInterface import *
from langdetect import detect


class LangDetect(ExtractorInterface):
    """This class implements LangDetect as an article extractor but it can only
    detect the extracted language (en, de, ...).

    :param pageTitle: A string, the pageTitle given from the database.
    """

    def __init__(self, page_title):
        self.page_title = page_title

    def name(self):
        """Returns the name of the article extractor."""
        return "langdetect"

    def language(self):
        """Returns the language of the extracted article using the pageTitle."""
        if self.page_title is not None:
            return detect(self.page_title)
        else:
            return None

    def title(self):
        """LangDetect can not extract the title."""
        return None

    def description(self):
        """LangDetect can not extract the description."""
        return None

    def text(self):
        """LangDetect can not extract the text."""
        return None

    def topimage(self):
        """LangDetect can not extract the topimage."""
        return None

    def author(self):
        """LangDetect can not extract the author."""
        return None

    def publish_date(self):
        """LangDetect can not extract the publish date."""
        return None