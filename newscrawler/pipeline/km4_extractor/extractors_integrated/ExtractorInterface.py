from abc import ABCMeta, abstractmethod


class ExtractorInterface(metaclass=ABCMeta):
    """Abstract class for article extractors_integrated. Every method has
    to be redefined in the subclass.
    """

    @abstractmethod
    def name(self):
        """Returns the name of the article extractor."""
        return

    @abstractmethod
    def language(self):
        """Returns the language of the extracted article."""
        return

    @abstractmethod
    def title(self):
        """Returns the title of the extracted article."""
        return

    @abstractmethod
    def description(self):
        """Returns the description/lead paragraph of the extracted article."""
        return

    @abstractmethod
    def text(self):
        """Returns the main text of the extracted article."""
        return

    @abstractmethod
    def topimage(self):
        """Returns the top image of the extracted article."""
        return

    @abstractmethod
    def author(self):
        """Returns the authors of the extracted article."""
        return

    @abstractmethod
    def publish_date(self):
        """Returns the publish date of the extracted article."""
        return
