class ComparerDescription():
    """This class compares the descriptions of the list of ArticleCandidates and sends the result
    back to the Comparer.
    """

    def extract(self, item, list_article_candidate):
        """Compares the extracted descriptions.

        :param item: The corresponding NewscrawlerItem
        :param list_article_candidate: A list, the list of ArticleCandidate-Objects which have been extracted
        :return: A string, the most likely description
        """
        list_description = []

        """ The descriptions of the article candidates and the respective extractors are saved
        in a tuple in list_description.
        """
        for article_candidate in list_article_candidate:
            if article_candidate.description != None:
                list_description.append((article_candidate.description, article_candidate.extractor))

        # If there is no value in the list, return None.
        if len(list_description) == 0:
            return None

        # If there are more options than one, return the result from newspaper.
        list_newspaper = [x for x in list_description if x[1] == "newspaper"]
        if len(list_newspaper) == 0:

            # If there is no description extracted by newspaper, return the first result of list_description.
            return list_description[0][0]
        else:
            return list_newspaper[0][0]
