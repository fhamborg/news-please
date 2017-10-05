class NewsArticle(object):
    """
    Class representing a single news article containing all the information that news-please can extract.
    """
    authors = []
    date_download = None
    date_modify = None
    date_publish = None
    description = None
    filename = None
    image_url = None
    language = None
    localpath = None
    source_domain = None
    text = None
    title = None
    title_page = None
    title_rss = None
    url = None

    def get_dict(self):
        """
        Get the dict of the instance of this class.
        :return:
        """
        return {
            'authors': self.authors,
            'date_download': self.date_download,
            'date_modify': self.date_modify,
            'date_publish': self.date_publish,
            'description': self.description,
            'filename': self.filename,
            'image_url': self.image_url,
            'language': self.language,
            'localpath': self.localpath,
            'source_domain': self.source_domain,
            'text': self.text,
            'title': self.title,
            'title_page': self.title_page,
            'title_rss': self.title_rss,
            'url': self.url
        }
