class NewsArticle(dict):
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
        return self.__dict__
