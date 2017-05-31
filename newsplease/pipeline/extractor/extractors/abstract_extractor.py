from abc import ABCMeta, abstractmethod

from ..article_candidate import ArticleCandidate


class AbstractExtractor:
    """Abstract class for article extractors.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self):
        self.name = None

    def _name(self):
        """Returns the name of the article extractor."""
        return self.name

    def _language(self, item):
        """Returns the language of the extracted article."""
        return None

    def _title(self, item):
        """Returns the title of the extracted article."""
        return None

    def _description(self, item):
        """Returns the description/lead paragraph of the extracted article."""
        return None

    def _text(self, item):
        """Returns the main text of the extracted article."""
        return None

    def _topimage(self, item):
        """Returns the top image of the extracted article."""
        return None

    def _author(self, item):
        """Returns the authors of the extracted article."""
        return None

    def _publish_date(self, item):
        """Returns the publish date of the extracted article."""
        return None

    def extract(self, item):
        """Executes all implemented functions on the given article and returns an
        object containing the recovered data.

        :param item: A NewscrawlerItem to parse.
        :return: ArticleCandidate containing the recovered article data.
        """

        article_candidate = ArticleCandidate()
        article_candidate.extractor = self._name()
        article_candidate.title = self._title(item)
        article_candidate.description = self._description(item)
        article_candidate.text = self._text(item)
        article_candidate.topimage = self._topimage(item)
        article_candidate.author = self._author(item)
        article_candidate.publish_date = self._publish_date(item)
        article_candidate.language = self._language(item)

        return article_candidate
