class ComparerLanguage:
    """Implements a compare method for detected languages"""

    def extract(self, item, list_article_candidate):
        """Compares how often any language was detected.

        :param item: The corresponding NewscrawlerItem
        :param list_article_candidate: A list, the list of ArticleCandidate-Objects which have been extracted
        :return: A string, the language which was most frequently detected
        """

        # Save extracted languages in list
        languages_extracted = []

        # Save the extracted language of newspaper in extra variable, because newspaper extract meta-language
        # which is very accurate.
        language_newspaper = None

        for article_candidate in list_article_candidate:

            if article_candidate.language is not None:
                languages_extracted.append(article_candidate.language)

                if article_candidate.extractor == "newspaper":
                    language_newspaper = article_candidate.language

        if not languages_extracted:
            return None

        # Create a set of the extracted languages, so every lang appears once
        languages_extracted_set = set(languages_extracted)

        # Count how often every language has been extracted
        languages_extracted_number = []

        for language in languages_extracted_set:
            languages_extracted_number.append((languages_extracted.count(language), language))

        if not (languages_extracted_number):
            return None

        # If there is no favorite language, return the language extracted by newspaper
        if max(languages_extracted_number)[0] == min(languages_extracted_number)[0] and language_newspaper is not None:
            return language_newspaper

        if languages_extracted_number:
            return (max(languages_extracted_number))[1]
        else:
            return None
