from src.extractors_integrated.ExtractorInterface import *
# Import Newspaper Article Extractor Library.
from newspaper import Article


class Newspaper(ExtractorInterface, Article):
    """This class implements Newspaper as an article extractor. Newspaper is
    a subclass of Extractors and newspaper.Article
    """

    def __init__(self, html):
        """Creates an instance of Article without downloading it.
        It uses the local downloaded html-file instead and parses the given file.

        :param html: A string, the html document
        """
        self.html = html
        self.article = Article("")
        self.article.set_html(self.html)
        self.article.parse()

    def name(self):
        """Returns the name of the article extractor."""
        name = "newspaper"
        return name

    def language(self):
        """Returns the meta language tag from the extracted html."""
        return self.article.meta_lang

    def title(self):
        """Returns the title of the extracted article."""
        title = self.article.title
        return title

    def description(self):
        """Returns the description/lead paragraph of the extracted article."""
        description = self.article.meta_description
        return description

    def text(self):
        """Returns the main text of the extracted article."""
        text = self.article.text
        return text

    def author(self):
        """Returns the authors of the extracted article."""
        author = self.article.authors
        return author

    def topimage(self):
        """Returns the top image of the extracted article."""
        topimage = self.article.top_image
        return topimage

    def publish_date(self):
        """Returns the publish date of the extracted article."""
        publish_date = self.article.publish_date
        return publish_date
