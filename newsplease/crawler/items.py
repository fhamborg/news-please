# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewscrawlerItem(scrapy.Item):
    # ID of the article in the DB
    db_id = scrapy.Field()
    # Path of the file on the local filesystem
    local_path = scrapy.Field()
    # Filename
    filename = scrapy.Field()
    # absolute path of the file on the local filesystem
    abs_local_path = scrapy.Field()
    # When the article was last modified in the DB
    modified_date = scrapy.Field()
    # When the article was downloaded in the DB
    download_date = scrapy.Field()
    # Root domain from which the article came
    source_domain = scrapy.Field()
    url = scrapy.Field()
    # Title of the article
    html_title = scrapy.Field()
    # Response object from crawler
    spider_response = scrapy.Field()
    # Title of the article as store in the RSS feed
    rss_title = scrapy.Field()
    # Extracted article title
    article_title = scrapy.Field()
    # Extracted article description
    article_description = scrapy.Field()
    # Extracted article text body
    article_text = scrapy.Field()
    # Extracted top image of the article
    article_image = scrapy.Field()
    # Extracted article author
    article_author = scrapy.Field()
    # Extracted publishing date
    article_publish_date = scrapy.Field()
    # Extracted language of the article
    article_language = scrapy.Field()
