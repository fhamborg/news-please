import itertools


class ComparerText():
    """This class compares the text of the list of ArticleCandidates and sends the result back to the Comparer."""

    def extract(self, item, article_candidate_list):
        """Compares the extracted texts.

        :param item: The corresponding NewscrawlerItem
        :param article_candidate_list: A list, the list of ArticleCandidate-Objects which have been extracted
        :return: A string, the most likely text
        """
        list_text = []

        # The minimal number of words a text needs to have
        min_number_words = 15

        # The texts of the article candidates and the respective extractors are saved in a tuple in list_text.
        for article_candidate in article_candidate_list:
            if article_candidate.text != None:
                list_text.append((article_candidate.text, article_candidate.extractor))

        # Remove texts that are shorter than min_number_words.
        for text_tuple in list_text:
            if len(text_tuple[0].split()) < min_number_words:
                list_text.remove(text_tuple)

        # If there is no value in the list, return None.
        if len(list_text) == 0:
            return None

        # If there is only one solution, return it.
        if len(list_text) < 2:
            return list_text[0][0]
        else:

            # If there is more than one solution, do the following:

            # Create a list which holds triple of the score and the two extractors
            list_score = []

            # Compare every text with all other texts at least once
            for a, b, in itertools.combinations(list_text, 2):

                # Create sets from the texts
                set_a = set(a[0].split())
                set_b = set(b[0].split())
                symmetric_difference_a_b = set_a ^ set_b
                intersection_a_b = set_a & set_b

                # Replace 0 with -1 in order to elude division by zero
                if intersection_a_b == 0:
                    intersection_a_b = -1

                # Create the score. It divides the number of words which are not in both texts by the number of words which
                # are in both texts and subtracts the result from 1. The closer to 1 the more similiar they are.
                score = 1 - ((len(symmetric_difference_a_b)) / (2 * len(intersection_a_b)))
                list_score.append((score, a[1], b[1]))

            # Find out which is the highest score
            best_score = max(list_score, key=lambda item: item[0])

            # If one of the solutions is newspaper return it
            if "newspaper" in best_score:
                return (list(filter(lambda x: x[1] == "newspaper", list_text))[0][0])
            else:
                # If not, return the text that is longer

                # A list that holds the extracted texts and their extractors which were most similar
                top_candidates = []
                for tuple in list_text:
                    if tuple[1] == best_score[1] or tuple[1] == best_score[2]:
                        top_candidates.append(tuple)

                if len(top_candidates[0][0]) > len(top_candidates[1][0]):
                    return (top_candidates[0][0])
                else:
                    return (top_candidates[1][0])
