
class ArticleRaw:
    """This is a helpclass to store an article after downloading it from the database.
    It contains the raw html data and other Informations from the Database
    Creates an instance of ArticleRaw and opens the html-file.
    """
    def __init__(self):
        self.id = None
        self.localpath = None
        self.modifie_date = None
        self.download_date = None
        self.source_domain = None
        self.url = None
        self.page_title = None
        self.ancestor = None
        self.descendant = None
        self.version = None
        self.rss_title = None
        self.html = None

    def tupel_to_article_raw(self, article):
            self.id = article[0]
            self.localpath = article[1]
            self.modified_date = article[2]
            self.download_date = article[3]
            #self.source_domain = article[4]
            #self.url = article[5]
            #self.page_title = article[6]
            #self.ancestor = article[7]
            #self.descendant = article[8]
            #self.version = article[9]
            #self.rss_title = article[10]






