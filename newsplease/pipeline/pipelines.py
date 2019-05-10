# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime
import json
import logging
import os.path
import sys

import pymysql
from dateutil import parser as dateparser
from elasticsearch import Elasticsearch
from scrapy.exceptions import DropItem

from NewsArticle import NewsArticle
from .extractor import article_extractor
from ..config import CrawlerConfig

if sys.version_info[0] < 3:
    ConnectionError = OSError

try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = None
    pd = None


class HTMLCodeHandling(object):
    """
    Handles reponses to HTML responses other than 200 (accept).
    As of 22.06.16 not active, but serves as an example of new
    functionality
    """

    def process_item(self, item, spider):
        # For the case where something goes wrong
        if item['spider_response'].status != 200:
            # Item is no longer processed in the pipeline
            raise DropItem("%s: Non-200 response" % item['url'])
        else:
            return item


class ArticleMasterExtractor(object):
    """
    Parses the HTML response and extracts title, description,
    text, image and meta data of an article.
    """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.cfg = CrawlerConfig.get_instance()
        self.extractor_list = self.cfg.section("ArticleMasterExtractor")[
            "extractors"]

        self.extractor = article_extractor.Extractor(self.extractor_list)

    def process_item(self, item, spider):
        return self.extractor.extract(item)


class RSSCrawlCompare(object):
    """
    Compares the item's age to the current version in the DB.
    If the difference is greater than delta_time, then save the newer version.
    """
    log = None
    cfg = None
    delta_time = None
    database = None
    conn = None
    cursor = None

    # Defined DB query to retrieve the last version of the article
    compare_versions = ("SELECT * FROM CurrentVersions WHERE url=%s")

    def __init__(self):
        self.log = logging.getLogger(__name__)

        self.cfg = CrawlerConfig.get_instance()
        self.delta_time = self.cfg.section("Crawler")[
            "hours_to_pass_for_redownload_by_rss_crawler"]
        self.database = self.cfg.section("MySQL")

        # Establish DB connection
        # Closing of the connection is handled once the spider closes
        self.conn = pymysql.connect(host=self.database["host"],
                                    port=self.database["port"],
                                    db=self.database["db"],
                                    user=self.database["username"],
                                    passwd=self.database["password"])
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        if spider.name in ['RssCrawler', 'GdeltCrawler']:
            # Search the CurrentVersion table for a version of the article
            try:
                self.cursor.execute(self.compare_versions, (item['url'],))
            except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError,
                    pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in rss query: %s", error)

            # Save the result of the query. Must be done before the add,
            #   otherwise the result will be overwritten in the buffer
            old_version = self.cursor.fetchone()

            if old_version is not None and (datetime.datetime.strptime(
                    item['download_date'], "%y-%m-%d %H:%M:%S") -
                                            old_version[3]) \
                    < datetime.timedelta(hours=self.delta_time):
                # Compare the two download dates. index 3 of old_version
                # corresponds to the download_date attribute in the DB
                raise DropItem("Article in DB too recent. Not saving.")

        return item

    def close_spider(self, spider):
        # Close DB connection - garbage collection
        self.conn.close()


class MySQLStorage(object):
    """
    Handles remote storage of the meta data in the DB
    """

    log = None
    cfg = None
    database = None
    conn = None
    cursor = None
    # initialize necessary DB queries for this pipe
    compare_versions = ("SELECT * FROM CurrentVersions WHERE url=%s")
    insert_current = ("INSERT INTO CurrentVersions(local_path,\
                          modified_date,download_date,source_domain,url,\
                          html_title, ancestor, descendant, version,\
                          rss_title) VALUES (%(local_path)s,\
                          %(modified_date)s, %(download_date)s,\
                          %(source_domain)s, %(url)s, %(html_title)s,\
                          %(ancestor)s, %(descendant)s, %(version)s,\
                          %(rss_title)s)")

    insert_archive = ("INSERT INTO ArchiveVersions(id, local_path,\
                          modified_date,download_date,source_domain,url,\
                          html_title, ancestor, descendant, version,\
                          rss_title) VALUES (%(db_id)s, %(local_path)s,\
                          %(modified_date)s, %(download_date)s,\
                          %(source_domain)s, %(url)s, %(html_title)s,\
                          %(ancestor)s, %(descendant)s, %(version)s,\
                          %(rss_title)s)")

    delete_from_current = ("DELETE FROM CurrentVersions WHERE id = %s")

    # init database connection
    def __init__(self):
        self.log = logging.getLogger(__name__)

        self.cfg = CrawlerConfig.get_instance()
        self.database = self.cfg.section("MySQL")
        # Establish DB connection
        # Closing of the connection is handled once the spider closes
        self.conn = pymysql.connect(host=self.database["host"],
                                    port=self.database["port"],
                                    db=self.database["db"],
                                    user=self.database["username"],
                                    passwd=self.database["password"])
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        """
        Store item data in DB.
        First determine if a version of the article already exists,
          if so then 'migrate' the older version to the archive table.
        Second store the new article in the current version table
        """

        # Set defaults
        version = 1
        ancestor = 0

        # Search the CurrentVersion table for an old version of the article
        try:
            self.cursor.execute(self.compare_versions, (item['url'],))
        except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError,
                pymysql.IntegrityError, TypeError) as error:
            self.log.error("Something went wrong in query: %s", error)

        # Save the result of the query. Must be done before the add,
        # otherwise the result will be overwritten in the buffer
        old_version = self.cursor.fetchone()

        if old_version is not None:
            old_version_list = {
                'db_id': old_version[0],
                'local_path': old_version[1],
                'modified_date': old_version[2],
                'download_date': old_version[3],
                'source_domain': old_version[4],
                'url': old_version[5],
                'html_title': old_version[6],
                'ancestor': old_version[7],
                'descendant': old_version[8],
                'version': old_version[9],
                'rss_title': old_version[10], }

            # Update the version number and the ancestor variable for later references
            version = (old_version[9] + 1)
            ancestor = old_version[0]

        # Add the new version of the article to the CurrentVersion table
        current_version_list = {
            'local_path': item['local_path'],
            'modified_date': item['modified_date'],
            'download_date': item['download_date'],
            'source_domain': item['source_domain'],
            'url': item['url'],
            'html_title': item['html_title'],
            'ancestor': ancestor,
            'descendant': 0,
            'version': version,
            'rss_title': item['rss_title'], }

        try:
            self.cursor.execute(self.insert_current, current_version_list)
            self.conn.commit()
            self.log.info("Article inserted into the database.")
        except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError,
                pymysql.IntegrityError, TypeError) as error:
            self.log.error("Something went wrong in commit: %s", error)

        # Move the old version from the CurrentVersion table to the ArchiveVersions table
        if old_version is not None:
            # Set descendant attribute
            try:
                old_version_list['descendant'] = self.cursor.lastrowid
            except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError,
                    pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in id query: %s", error)

            # Delete the old version of the article from the CurrentVersion table
            try:
                self.cursor.execute(self.delete_from_current, old_version_list['db_id'])
                self.conn.commit()
            except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError,
                    pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in delete: %s", error)

            # Add the old version to the ArchiveVersion table
            try:
                self.cursor.execute(self.insert_archive, old_version_list)
                self.conn.commit()
                self.log.info("Moved old version of an article to the archive.")
            except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError,
                    pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in archive: %s", error)

        return item

    def close_spider(self, spider):
        # Close DB connection - garbage collection
        self.conn.close()


class ExtractedInformationStorage(object):
    """
    Provides basic functionality for Storages
    """

    log = None

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.cfg = CrawlerConfig.get_instance()

    @staticmethod
    def ensure_str(text):
        if isinstance(text, str):
            return text
        else:
            return text.decode('utf-8')

    @staticmethod
    def extract_relevant_info(item):
        """
        extracts from an item only fields that we want to output as extracted information
        :rtype: object
        :param item:
        :return:
        """
        article = {
            'authors': item['article_author'],
            'date_download': item['download_date'],
            'date_modify': item['modified_date'],
            'date_publish': item['article_publish_date'],
            'description': item['article_description'],
            'filename': item['filename'],
            'image_url': item['article_image'],
            'language': item['article_language'],
            'localpath': item['local_path'],
            'title': item['article_title'],
            'title_page': ExtractedInformationStorage.ensure_str(item['html_title']),
            'title_rss': ExtractedInformationStorage.ensure_str(item['rss_title']),
            'source_domain': ExtractedInformationStorage.ensure_str(item['source_domain']),
            'text': item['article_text'],
            'url': item['url']
        }

        # clean values
        for key in article:
            value = article[key]
            if isinstance(value, str) and not value:
                article[key] = None

        return article

    @staticmethod
    def datestring_to_date(text):
        if text:
            return dateparser.parse(text)
        else:
            return None

    @staticmethod
    def convert_to_class(item):
        news_article = NewsArticle()
        news_article.authors = item['authors']
        news_article.date_download = ExtractedInformationStorage.datestring_to_date(item['date_download'])
        news_article.date_modify = ExtractedInformationStorage.datestring_to_date(item['date_modify'])
        news_article.date_publish = ExtractedInformationStorage.datestring_to_date(item['date_publish'])
        news_article.description = item['description']
        news_article.filename = item['filename']
        news_article.image_url = item['image_url']
        news_article.language = item['language']
        news_article.localpath = item['localpath']
        news_article.title = item['title']
        news_article.title_page = item['title_page']
        news_article.title_rss = item['title_rss']
        news_article.source_domain = item['source_domain']
        news_article.text = item['text']
        news_article.url = item['url']
        return news_article


class InMemoryStorage(ExtractedInformationStorage):
    """
    Stores extracted information in a dictionary in memory - for use with library mode.
    """

    results = {}  # this is a static variable

    def process_item(self, item, spider):
        # get the original url, so that the library class (or whoever wants to read this) can access the article
        if 'redirect_urls' in item._values['spider_response'].meta:
            url = item._values['spider_response'].meta['redirect_urls'][0]
        else:
            url = item._values['url']
        InMemoryStorage.results[url] = ExtractedInformationStorage.extract_relevant_info(item)
        return item

    @staticmethod
    def get_results():
        return InMemoryStorage.results


class HtmlFileStorage(ExtractedInformationStorage):
    """
    Handles storage of the file on the local system
    """

    # Save the html and filename to the local storage folder
    def process_item(self, item, spider):
        # Add a log entry confirming the save
        self.log.info("Saving HTML to %s", item['abs_local_path'])

        # Ensure path exists
        dir_ = os.path.dirname(item['abs_local_path'])
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        # Write raw html to local file system
        with open(item['abs_local_path'], 'wb') as file_:
            file_.write(item['spider_response'].body)

        return item


class JsonFileStorage(ExtractedInformationStorage):
    """
    Handles remote storage of the data in Json files
    """

    log = None
    cfg = None

    def process_item(self, item, spider):
        file_path = item['abs_local_path'] + '.json'

        # Add a log entry confirming the save
        self.log.info("Saving JSON to %s", file_path)

        # Ensure path exists
        dir_ = os.path.dirname(item['abs_local_path'])
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        # Write JSON to local file system
        with open(file_path, 'w') as file_:
            json.dump(ExtractedInformationStorage.extract_relevant_info(item), file_, ensure_ascii=False)

        return item


class ElasticsearchStorage(ExtractedInformationStorage):
    """
    Handles remote storage of the meta data in Elasticsearch
    """

    log = None
    cfg = None
    es = None
    index_current = None
    index_archive = None
    mapping = None
    running = False

    def __init__(self):
        self.log = logging.getLogger('elasticsearch.trace')
        self.log.addHandler(logging.NullHandler())
        self.cfg = CrawlerConfig.get_instance()
        self.database = self.cfg.section("Elasticsearch")

        self.es = Elasticsearch([self.database["host"]],
                                http_auth=(str(self.database["username"]), str(self.database["secret"])),
                                port=self.database["port"],
                                use_ssl=self.database["use_ca_certificates"],
                                verify_certs=self.database["use_ca_certificates"],
                                ca_certs=self.database["ca_cert_path"],
                                client_cert=self.database["client_cert_path"],
                                client_key=self.database["client_key_path"])
        self.index_current = self.database["index_current"]
        self.index_archive = self.database["index_archive"]
        self.mapping = self.database["mapping"]

        # check connection to Database and set the configuration

        try:
            # check if server is available
            self.es.ping()

            # raise logging level due to indices.exists() habit of logging a warning if an index doesn't exist.
            es_log = logging.getLogger('elasticsearch')
            es_level = es_log.getEffectiveLevel()
            es_log.setLevel('ERROR')

            # check if the necessary indices exist and create them if needed
            if not self.es.indices.exists(self.index_current):
                self.es.indices.create(index=self.index_current, ignore=[400, 404])
                self.es.indices.put_mapping(index=self.index_current, doc_type='_doc', body=self.mapping)
            if not self.es.indices.exists(self.index_archive):
                self.es.indices.create(index=self.index_archive, ignore=[400, 404])
                self.es.indices.put_mapping(index=self.index_archive, doc_type='_doc', body=self.mapping)
            self.running = True

            # restore previous logging level
            es_log.setLevel(es_level)

        except ConnectionError as error:
            self.running = False
            self.log.error("Failed to connect to Elasticsearch, this module will be deactivated. "
                           "Please check if the database is running and the config is correct: %s" % error)

    def process_item(self, item, spider):

        if self.running:
            try:
                version = 1
                ancestor = None

                # search for previous version
                request = self.es.search(index=self.index_current, body={'query': {'match': {'url.keyword': item['url']}}})
                if request['hits']['total'] > 0:
                    # save old version into index_archive
                    old_version = request['hits']['hits'][0]
                    old_version['_source']['descendent'] = True
                    self.es.index(index=self.index_archive, doc_type='_doc', body=old_version['_source'])
                    version += 1
                    ancestor = old_version['_id']

                # save new version into old id of index_current
                self.log.info("Saving to Elasticsearch: %s" % item['url'])
                extracted_info = ExtractedInformationStorage.extract_relevant_info(item)
                extracted_info['ancestor'] = ancestor
                extracted_info['version'] = version
                self.es.index(index=self.index_current, doc_type='_doc', id=ancestor,
                              body=extracted_info)


            except ConnectionError as error:
                self.running = False
                self.log.error("Lost connection to Elasticsearch, this module will be deactivated: %s" % error)
        return item


class DateFilter(object):
    """
    Filters articles based on their publishing date, articles with a date outside of a specified interval are dropped.
    This module should be placed after the KM4 article extractor.
    """

    log = None
    cfg = None
    strict_mode = False
    start_date = None
    end_date = None

    def __init__(self):
        self.log = logging.getLogger(__name__ + '.DateFilter')
        self.cfg = CrawlerConfig.get_instance()
        self.config = self.cfg.section("DateFilter")
        self.strict_mode = self.config['strict_mode']
        self.start_date = self.config['start_date']
        self.end_date = self.config['end_date']

        if self.start_date is None and self.end_date is None:
            self.log.error("DateFilter: No dates are defined, please check the configuration of this module.")
        else:
            # create datetime objects from given dates
            try:
                if self.start_date is not None:
                    self.start_date = datetime.datetime.strptime(str(self.start_date), '%Y-%m-%d %H:%M:%S')
                if self.end_date is not None:
                    self.end_date = datetime.datetime.strptime(str(self.end_date), '%Y-%m-%d %H:%M:%S')
            except ValueError as error:
                self.start_date = None
                self.end_date = None
                self.log.error("DateFilter: Couldn't read start or end date of the specified interval. "
                               "The Filter is now deactivated."
                               "Please check the configuration of this module and be sure follow the format "
                               "'yyyy-mm-dd hh:mm:ss' for dates or set the variables to None.")

    def process_item(self, item, spider):

        # Check if date could be extracted
        if item['article_publish_date'] is None and self.strict_mode:
            raise DropItem('DateFilter: %s: Publishing date is missing and strict mode is enabled.' % item['url'])
        elif item['article_publish_date'] is None:
            return item
        else:
            # Create datetime object
            try:
                publish_date = datetime.datetime.strptime(str(item['article_publish_date']), '%Y-%m-%d %H:%M:%S')
            except ValueError as error:
                self.log.warning("DateFilter: Extracted date has the wrong format: %s - %s" %
                                 (item['article_publishing_date'], item['url']))
                if self.strict_mode:
                    raise DropItem('DateFilter: %s: Dropped due to wrong date format: %s' %
                                   (item['url'], item['publish_date']))
                else:
                    return item
            # Check interval boundaries
            if self.start_date is not None and self.start_date > publish_date:
                raise DropItem('DateFilter: %s: Article is too old: %s' % (item['url'], publish_date))
            elif self.end_date is not None and self.end_date < publish_date:
                raise DropItem('DateFilter: %s: Article is too young: %s ' % (item['url'], publish_date))
            else:
                return item


class PandasStorage(ExtractedInformationStorage):
    """
    Store meta data a Pandas data frame
    """

    log = None
    cfg = None
    es = None
    index_current = None
    index_archive = None
    mapping = None
    running = False

    def __init__(self):
        if np is None:
            raise ModuleNotFoundError("Using PandasStorage requires numpy and pandas")
        self.log = logging.getLogger(__name__)
        self.cfg = CrawlerConfig.get_instance()
        self.database = self.cfg.section("Pandas")

        df_index = "url"
        columns = [
            "source_domain", "title_page", "title_rss", "localpath", "filename",
            "date_download", "date_modify", "date_publish", "title", "description",
            "text", "authors", "image_url", "language", 'url'
        ]

        working_path = self.cfg.section("Files")['working_path']
        file_name = self.database['file_name']
        self.full_path = os.path.join(working_path, file_name, '.pickle')

        try:
            self.df = pd.read_pickle(self.full_path)
            self.log.info(
                "Found existing Pandas file with %i rows at %s", len(self.df),
                self.full_path
            )
            for col in columns:
                if col not in self.df.columns:
                    raise KeyError(col)
        except FileNotFoundError:
            self.df = pd.DataFrame(columns=columns.keys())
            self.log.info("Created new Pandas file at '%s'", self.full_path)
            self.df.set_index(df_index, inplace=True, drop=False)
        except KeyError as e:
            self.log.error("%s is missing a column.", self.full_path)
            raise e

    def process_item(self, item, _spider):
        article = {
            'authors': item['article_author'],
            'date_download': item['download_date'],
            'date_modify': item['modified_date'],
            'date_publish': item['article_publish_date'],
            'description': item['article_description'],
            'filename': item['filename'],
            'image_url': item['article_image'],
            'language': item['article_language'],
            'localpath': item['local_path'],
            'title': item['article_title'],
            'title_page': ExtractedInformationStorage.ensure_str(item['html_title']),
            'title_rss': ExtractedInformationStorage.ensure_str(item['rss_title']),
            'source_domain':
            ExtractedInformationStorage.ensure_str(item['source_domain']),
            'text': item['article_text'],
            'url': item['url']
        }
        self.df.loc[item['url']] = article
        return item

    def close_spider(self, _spider):
        """
        Write out to file
        """
        self.df['date_download'] = pd.to_datetime(
            self.df['date_download'], errors='coerce', infer_datetime_format=True
        )
        self.df['date_modify'] = pd.to_datetime(
            self.df['date_modify'], errors='coerce', infer_datetime_format=True
        )
        self.df['date_publish'] = pd.to_datetime(
            self.df['date_publish'], errors='coerce', infer_datetime_format=True
        )
        self.df.to_pickle(self.full_path)
        self.log.info("Wrote to Pandas to %s", self.full_path)
