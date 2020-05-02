from abc import ABCMeta, abstractmethod


class AbstractAnalyzer:
    """Abstract class for article extractors.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self):
        self.name = None

    def _name(self):
        """Returns the name of the article extractor."""
        return self.name

    @abstractmethod
    def get_result(self, item):
        raise NotImplementedError

    def analyze(self, item):
        """Executes all implemented functions on the given item and returns an
        object conainting the analysis informatiion

        :param item: A NewscrawlerItem to parse.
        :return: insight:.
        """
        analysis_result = self.get_result(item)
        return analysis_result
