import re
from urllib.parse import urljoin

class Article():
    """This is a helpclass to store the final result of an article, after it was extracted, cleaned, and compared."""

    def __init__(self):
        self.title = None
        self.description = None
        self.text = None
        self.topimage = None
        self.author = None
        self.publish_date = None
        self.language = None
        self.id = None
        self.localpath = None
        self.modified_date = None
        self.download_date = None
        self.source_domain = None
        self.url = None
        self.page_title = None
        self.ancestor = None
        self.descendant = None
        self.version = None
        self.rss_title = None
        self.html = None

    def merge_with_articleraw(self, articleraw):
        """Saves the information from the database in the article-object.

        :param articleraw: An ArticleRaw-Object, the raw article with the information's from the database
        """
        self.id = articleraw.id
        self.localpath = articleraw.localpath
        self.modified_date = articleraw.modified_date
        self.download_date = articleraw.download_date
        self.source_domain = articleraw.source_domain
        self.url = articleraw.url
        self.page_title = articleraw.page_title
        self.ancestor = articleraw.ancestor
        self.descendant = articleraw.descendant
        self.version = articleraw.version
        self.rss_title = articleraw.rss_title
