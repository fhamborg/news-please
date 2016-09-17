import bleach
from readability import Document
from src.extractors_integrated.ExtractorInterface import *


class Readability(ExtractorInterface, Document):
    """This class implements Readability as an article extractor. Readability is
    a subclass of Extractors and newspaper.Article.

    :param html: A string, the html document
    """

    def __init__(self, html):
        self.html = html

    def name(self):
        name = "readability"
        return None # name

    def language(self):
        """Readability can't extract the language."""
        return None

    def title(self):
        """Returns the title of the extracted article."""
        title = Document(self.html).short_title()
        return title

    def description(self):
        """readability can't extract the lead paragraph."""
        return None

    def text(self):
        """Returns the main text of the extracted article."""
        text = Document(self.html).summary()
        ctext = bleach.clean(text, strip=True)
        return ctext

    def topimage(self):
        return None

    def author(self):
        """Readability can't extract the authors."""
        return None

    def publish_date(self):
        return None