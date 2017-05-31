import re

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


class ComparerTopimage():
    """This class compares the topimages of the list of ArticleCandidates and sends the result back to the Comparer."""

    def extract(self, item, list_article_candidate):
        """Compares the extracted top images.

        :param item: The corresponding NewscrawlerItem
        :param list_article_candidate: A list, the list of ArticleCandidate-Objects which have been extracted
        :return: A string (url), the most likely top image
        """
        list_topimage = []

        for article_candidate in list_article_candidate:
            if article_candidate.topimage is not None:
                # Changes a relative path of an image to the absolute path of the given url.
                article_candidate.topimage = self.image_absoulte_path(item['url'], article_candidate.topimage)
                list_topimage.append((article_candidate.topimage, article_candidate.extractor))

        # If there is no value in the list, return None.
        if len(list_topimage) == 0:
            return None

        # If there are more options than one, return the result from newspaper.
        list_newspaper = [x for x in list_topimage if x[1] == "newspaper"]
        if len(list_newspaper) == 0:

            # If there is no topimage extracted by newspaper, return the first result of list_topimage.
            return list_topimage[0][0]
        else:
            return list_newspaper[0][0]

    def image_absoulte_path(self, url, image):
        """if the image url does not start with 'http://' it will take the absolute path from the url
        and fuses them with urljoin"""
        if not re.match('http://*', image):
            topimage = urljoin(url, image)
            return topimage
        return image
