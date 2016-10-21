from newscrawler.pipeline.km4_extractor.article_candidate import ArticleCandidate
from newscrawler.pipeline.km4_extractor.comparer.comparer_title import *
from newscrawler.pipeline.km4_extractor.comparer.comparer_description import *
from newscrawler.pipeline.km4_extractor.comparer.comparer_text import *
from newscrawler.pipeline.km4_extractor.comparer.comparer_topimage import *
from newscrawler.pipeline.km4_extractor.comparer.comparer_author import *
from newscrawler.pipeline.km4_extractor.comparer.comparer_date import *
from newscrawler.pipeline.km4_extractor.comparer.comparer_Language import *


class Comparer:
    """This class sends the list of ArticleCandidates to the subcomparer and saves the result in Article."""

    # Create subcomparer
    def __init__(self):
        self.comparer_title = ComparerTitle()
        self.comparer_desciption = ComparerDescription()
        self.comparer_text = ComparerText()
        self.comparer_topimage = ComparerTopimage()
        self.comparer_author = ComparerAuthor()
        self.comparer_date = ComparerDate()
        self.comparer_language = ComparerLanguage()

    def compare(self, item, article_candidates):
        """Compares the article candidates using the different submodules and saves the best results in
        new ArticleCandidate object

        :param article_candidates: The list of ArticleCandidate-Objects which have been extracted
        :return: An ArticleCandidate-object containing the best results
        """

        result = ArticleCandidate()

        result.title = self.comparer_title.extract(item, article_candidates)
        result.description = self.comparer_desciption.extract(item, article_candidates)
        result.text = self.comparer_text.extract(item, article_candidates)
        result.topimage = self.comparer_topimage.extract(item, article_candidates)
        result.author = self.comparer_author.extract(item, article_candidates)
        result.publish_date = self.comparer_date.extract(item, article_candidates)
        result.language = self.comparer_language.extract(item, article_candidates)
        return result
