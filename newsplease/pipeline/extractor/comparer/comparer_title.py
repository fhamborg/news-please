import itertools


class ComparerTitle():
    """This class compares the title if the list of ArticleCandidates and sends the result back to the Comparer."""

    def find_matches(self, list_title):
        """Checks if there are any matches between extracted titles.

        :param list_title: A list, the extracted titles saved in a list
        :return: A list, the matched titles
        """
        list_title_matches = []
        # Generate every possible tuple of titles and safe the matched string in a list.
        for a, b, in itertools.combinations(list_title, 2):
            if a == b:
                list_title_matches.append(a)

        return list_title_matches

    def extract_match(self, list_title_matches):
        """Extract the title with the most matches from the list.

        :param list_title_matches: A list, the extracted titles which match with others
        :return: A string, the most frequently extracted title.
        """
        # Create a set of the extracted titles
        list_title_matches_set = set(list_title_matches)

        list_title_count = []
        # Count how often a title was matched and safe as tuple in list.
        for match in list_title_matches_set:
            list_title_count.append((list_title_matches.count(match), match))

        if list_title_count and max(list_title_count)[0] != min(list_title_count)[0]:
            return max(list_title_count)[1]

        return None

    def choose_shortest_title(self, list_title):
        """Compares length of titles and returns the shortest one.

        :param list_title: A list, the extracted titles saved in a list
        :return: A string, the shortest title
        """
        list_length_string = []

        for title in list_title:
            list_length_string.append((len(title), title))

        return (min(list_length_string))[1]

    def extract(self, item, list_article_candidate):
        """Compares the extracted titles.

        :param item: The corresponding NewscrawlerItem
        :param list_article_candidate: A list, the list of ArticleCandidate-Objects which have been extracted
        :return: A string, the most likely title
        """
        list_title = []

        # Save every title from the candidates in list_title.
        for article_candidate in list_article_candidate:
            if article_candidate.title is not None:
                list_title.append(article_candidate.title)

        if not list_title:
            return None

        # Creates a list with matched titles
        list_title_matches = self.find_matches(list_title)
        # Extract title with the most matches
        matched_title = self.extract_match(list_title_matches)

        # Returns the matched title if there is one, else returns the shortest title
        if matched_title:
            return matched_title
        else:
            if list_title_matches:
                return self.choose_shortest_title(set(list_title_matches))
            else:
                return self.choose_shortest_title(list_title)
