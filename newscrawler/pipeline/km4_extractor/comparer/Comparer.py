from src.comparer.ComparerTitle import *
from src.comparer.ComparerDescription import *
from src.comparer.ComparerText import *
from src.comparer.ComparerTopimage import *
from src.comparer.ComparerAuthor import *
from src.comparer.ComparerDate import *
from src.comparer.ComparerLanguage import *


class Comparer():
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

    def compare(self, list_article_candidate, article):
        """Give list_article_candidate to different subcomparer.

        :param list_article_candidate: A list, the list of ArticleCandidate-Objects which have been extracted
        :param article: An Article-Object, the empty article
        :return: An Article-Object, the finally extracted article
        """
        article.title = self.comparer_title.extract(list_article_candidate)
        article.description = self.comparer_desciption.extract(list_article_candidate)
        article.text = self.comparer_text.extract(list_article_candidate)
        article.topimage = self.comparer_topimage.extract(list_article_candidate)
        article.author = self.comparer_author.extract(list_article_candidate)
        article.publish_date = self.comparer_date.extract(list_article_candidate)
        article.language = self.comparer_language.extract(list_article_candidate)
        return article
