import logging

from newspaper import Article

from .abstract_extractor import AbstractExtractor
from ..article_candidate import ArticleCandidate


class NewspaperExtractor(AbstractExtractor):
    """This class implements Newspaper as an article extractor. Newspaper is
    a subclass of ExtractorsInterface
    """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.name = "newspaper"

    def _article_kwargs(self):
        return {}

    def extract(self, item):
        """Creates an instance of Article without a Download and returns an ArticleCandidate with the results of
        parsing the HTML-Code.

        :param item: A NewscrawlerItem to parse.
        :return: ArticleCandidate containing the recovered article data.
        """
        article_candidate = ArticleCandidate()
        article_candidate.extractor = self._name()

        article = Article('', **self._article_kwargs())
        # old version of newspaper2k
        # article.set_html(item['spider_response'].body)
        # new version
        article.download(input_html=item['spider_response'].body, title=item['html_title'].decode())
        article.parse()
        article_candidate.title = article.title
        article_candidate.description = article.meta_description
        article_candidate.text = article.text
        article_candidate.topimage = article.top_image
        article_candidate.author = article.authors
        if article.publish_date:
            try:
                article_candidate.publish_date = article.publish_date.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError as exception:
                self.log.debug('%s: Newspaper failed to extract the date in the supported format,'
                              'Publishing date set to None' % item['url'])
        article_candidate.language = article.meta_lang

        return article_candidate
