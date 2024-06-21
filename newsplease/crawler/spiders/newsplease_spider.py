from abc import abstractmethod, ABC


class NewspleaseSpider(ABC):
    """
    Abstract base class for newsplease spiders.
    Defines methods that should be inherited by subclasses
    """

    @staticmethod
    @abstractmethod
    def supports_site(url: str) -> bool:
        """
        Determines if this spider works on the given URL.

        :param str url: The url to test
        :return bool:
        """
        pass

    @staticmethod
    def has_urls_to_scan(url: str) -> bool:
        """
        Determines if this spider has any URLs to scan.

        :param str url: The url to test
        :return bool:
        """
        return True
