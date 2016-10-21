# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import sys
import datetime
import os.path
import logging
import pymysql
from elasticsearch import Elasticsearch
from scrapy.exceptions import DropItem
from newscrawler.config import CrawlerConfig
from newscrawler.pipeline.km4_extractor import article_extractor
if sys.version_info[0] < 3:
    ConnectionError = OSError

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


class KM4ArticleExtractor(object):
    """
    Parses the HTML response and extracts title, description,
    text, image and meta data of an article.
    """

    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.cfg = CrawlerConfig.get_instance()
        self.extractor_list = self.cfg.section("KM4ArticleExtractor")[
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
        if spider.name == 'RssCrawler':
            # Search the CurrentVersion table for a version of the article
            try:
                self.cursor.execute(self.compare_versions, (item['url'],))
            except (pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in rss query: %s", error)

            # Save the result of the query. Must be done before the add,
            #   otherwise the result will be overwritten in the buffer
            old_version = self.cursor.fetchone()

            if old_version is not None:
                # Compare the two download dates. index 3 of old_version
                #   corresponds to the download_date attribute in the DB
                if (datetime.datetime.strptime(
                        item['download_date'], "%y-%m-%d %H:%M:%S") -
                        old_version[3]) \
                        < datetime.timedelta(hours=self.delta_time):
                    raise DropItem("Article in DB too recent. Not saving.")

        return item

    def close_spider(self, spider):
        # Close DB connection - garbage collection
        self.conn.close()


class DatabaseStorage(object):
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
        except (pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
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
        except (pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
            self.log.error("Something went wrong in commit: %s", error)

        # Move the old version from the CurrentVersion table to the ArchiveVersions table
        if old_version is not None:
            # Set descendant attribute
            try:
                old_version_list['descendant'] = self.cursor.lastrowid
            except (pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in id query: %s", error)

            # Delete the old version of the article from the CurrentVersion table
            try:
                self.cursor.execute(self.delete_from_current, old_version_list['db_id'])
                self.conn.commit()
            except (pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in delete: %s", error)

            # Add the old version to the ArchiveVersion table
            try:
                self.cursor.execute(self.insert_archive, old_version_list)
                self.conn.commit()
                self.log.info("Moved old version of an article to the archive.")
            except (pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
                self.log.error("Something went wrong in archive: %s", error)

        return item

    def close_spider(self, spider):
        # Close DB connection - garbage collection
        self.conn.close()


class LocalStorage(object):
    """
    Handles storage of the file on the local system
    """

    def __init__(self):
        self.log = logging.getLogger(__name__)

    # Save the html and filename to the local storage folder
    def process_item(self, item, spider):
        # Add a log entry confirming the save
        self.log.info("Saving to %s", item['abs_local_path'])

        # Ensure path exists
        dir_ = os.path.dirname(item['abs_local_path'])
        if not os.path.exists(dir_):
            os.makedirs(dir_)

        # Write raw html to local file system
        with open(item['abs_local_path'], 'wb') as file_:
            file_.write(item['spider_response'].body)

        return item


class ElasticSearchStorage(object):
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
        self.mapping = {'properties': self.database["mapping"]}

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
                self.es.indices.put_mapping(index=self.index_current, doc_type='article', body=self.mapping)
            if not self.es.indices.exists(self.index_archive):
                self.es.indices.create(index=self.index_archive, ignore=[400, 404])
                self.es.indices.put_mapping(index=self.index_archive, doc_type='article', body=self.mapping)
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
                request = self.es.search(index=self.index_current, body={'query': {'match': {'url': item['url']}}})
                if request['hits']['total'] > 0:
                    # save old version into index_archive
                    old_version = request['hits']['hits'][0]
                    old_version['_source']['descendent'] = True
                    self.es.index(index=self.index_archive, doc_type='article', body=old_version['_source'])
                    version += 1
                    ancestor = old_version['_id']

                # save new version into old id of index_current
                self.log.info("Saving to Elasticsearch: %s" % item['url'])
                self.es.index(index=self.index_current, doc_type='article', id=ancestor,
                              body={
                                'url': item['url'],
                                'sourceDomain': item['source_domain'].decode("utf-8"),
                                'pageTitle': item['html_title'].decode("utf-8"),
                                'rss_title': item['rss_title'],
                                'localpath': item['local_path'],
                                'ancestor': ancestor,
                                'descendant': False,
                                'version': version,
                                'downloadDate': item['download_date'],
                                'modifiedDate': item['modified_date'],
                                'publish_date': item['article_publish_date'],
                                'title': item['article_title'],
                                'description': item['article_description'],
                                'text': item['article_text'],
                                'author': item['article_author'],
                                'image': item['article_image'],
                                'language': item['article_language'],
                              })
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
                raise DropItem('DateFilter: %s: Article is to old: %s' % (item['url'], publish_date))
            elif self.end_date is not None and self.end_date < publish_date:
                raise DropItem('DateFilter: %s: Article is to young: %s ' % (item['url'], publish_date))
            else:
                return item


