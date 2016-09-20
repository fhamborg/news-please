from copy import deepcopy
from newscrawler.pipeline.km4_extractor.extractors.extractor_interface import *
# Import Newspaper Article Extractor Library.
from newspaper import Article


class Newspaper(ExtractorInterface):
    """This class implements Newspaper as an article extractor. Newspaper is
    a subclass of ExtractorsInterface
    """

    def __init__(self):
        self.name = "newspaper"

    def extract(self, item):
        """Creates an instance of Article without a Download and returns an ArticleCandidate with the results of
        parsing the HTML-Code.

        :param item: A NewscrawlerItem to parse.
        :return: ArticleCandidate containing the recovered article data.
        """

        article = Article('')
        article.set_html(deepcopy(item['spider_response']))
        article.parse()

        article_candidate = ArticleCandidate()
        article_candidate.extractor = self._name()
        article_candidate.title = article.title
        article_candidate.description = article.meta_description
        article_candidate.text = article.text
        article_candidate.topimage = article.top_image
        article_candidate.author = article.authors
        article_candidate.publish_date = article.publish_date
        article_candidate.language = article.meta_lang

        return article_candidate
