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
    # absolute path of the file on the local filesystem
    abs_local_path = scrapy.Field()
    # When the article was last modified
    modified_date = scrapy.Field()
    # When the article was downloaded
    download_date = scrapy.Field()
    # Root domain from which the article came
    source_domain = scrapy.Field()
    url = scrapy.Field()
    # Title of the article
    html_title = scrapy.Field()
    # Older version of the article in the DB, if exists
    ancestor = scrapy.Field()
    # Newer version of the article in the DB, if exists
    descendant = scrapy.Field()
    # Number of versions of the article in the DB
    version = scrapy.Field()
    # Reponse object from crawler
    spider_response = scrapy.Field()
    # Title of the article as store in the RSS feed
    rss_title = scrapy.Field()
