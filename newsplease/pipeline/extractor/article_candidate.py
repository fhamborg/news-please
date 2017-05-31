class ArticleCandidate:
    """This is a helpclass to store the result of an article after it was extracted. Every implemented extractor
    returns an ArticleCanditate as result.
    """
    url = None
    title = None
    description = None
    text = None
    topimage = None
    author = None
    publish_date = None
    extractor = None
    language = None
