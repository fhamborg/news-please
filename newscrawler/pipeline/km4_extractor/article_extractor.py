class Extractor:
    """This class initializes all extractors and saves the results of them. When adding a new extractor, it needs to
    be initialized here and added to list_extractor.
    """

    def __init__(self, extractor_list):
        """Initializes all the extractors with all other components.

        :param extractor_list: List containing all extractors to be initialized.
        """

        self.extractor_list = []
        for extractor in extractor_list:
            self.extractor_list.append(getattr(extractor, None))


    def extract(self, item):
        """Runs the HTML-response trough a list of initialized extractors.

        :param item: NewscrawlerItem to be processed.
        :return: A list, the extracted ArticleCandidate-Objects (One for each extractor)
        """

        article_candidates = []

        for extractor in self.extractor_list:
            article_candidates.append(extractor.extract(item['spider_response']))

        return item