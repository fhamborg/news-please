#!/usr/bin/env python
"""
Provides functionality to crawl and extract news articles from a single WARC file from commoncrawl.org. Filter criteria, such as publish date
and host list, can be defined. Currently, the WARC file will be downloaded to the path WORKINGDIR/cc_download_warc, if
not otherwise specified.
"""
import logging
import os
import sys
import time

from ago import human
import boto3
import botocore
from dateutil import parser
from hurry.filesize import size
from scrapy.utils.log import configure_logging
from six.moves import urllib
from warcio.archiveiterator import ArchiveIterator

from .. import NewsPlease, EmptyResponseError
from . import commoncrawl_crawler

__author__ = "Felix Hamborg"
__copyright__ = "Copyright 2017"
__credits__ = ["Sebastian Nagel"]


class CommonCrawlExtractor:
    # remote url where we can download the warc file
    __warc_path = None
    # download dir for warc files
    __local_download_dir_warc = './cc_download_warc/'
    # hosts (if None or empty list, any host is OK)
    __filter_valid_hosts = []  # example: ['elrancaguino.cl']
    # start date (if None, any date is OK as start date), as datetime
    __filter_start_date = None
    # end date (if None, any date is OK as end date)
    __filter_end_date = None
    # if date filtering is string, e.g., if we could not detect the date of an article, we will discard the article
    __filter_strict_date = True
    # if True, the script checks whether a file has been downloaded already and uses that file instead of downloading
    # again. Note that there is no check whether the file has been downloaded completely or is valid!
    __reuse_previously_downloaded_files = True
    # continue after error
    __continue_after_error = False
    # ignore unicode errors
    __ignore_unicode_errors = False
    # fetch images
    __fetch_images = False
    # log level
    __log_level = logging.INFO
    __delete_warc_after_extraction = True
    __log_pathname_fully_extracted_warcs = None

    # commoncrawl.org
    __cc_base_url = 'https://data.commoncrawl.org/'
    __cc_bucket = 'commoncrawl'
    __cc_news_crawl_names = None

    # event handler called when an article was extracted successfully and passed all filter criteria
    __callback_on_article_extracted = None
    # event handler called when a warc file is fully processed
    __callback_on_warc_completed = None
    # if the download progress is shown
    __show_download_progress = False

    # logging
    logging.basicConfig(level=__log_level)
    __logger = logging.getLogger(__name__)

    def __setup(self):
        """
        Setup
        :return:
        """
        os.makedirs(self.__local_download_dir_warc, exist_ok=True)

        # make loggers quiet
        configure_logging({"LOG_LEVEL": "ERROR"})
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.getLogger('readability').setLevel(logging.CRITICAL)
        logging.getLogger('PIL').setLevel(logging.CRITICAL)
        logging.getLogger('newspaper').setLevel(logging.CRITICAL)
        logging.getLogger('newsplease').setLevel(logging.CRITICAL)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)

        boto3.set_stream_logger('botocore', self.__log_level)
        boto3.set_stream_logger('boto3', self.__log_level)
        boto3.set_stream_logger('s3transfer', self.__log_level)

        # set own logger
        logging.basicConfig(level=self.__log_level)
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(self.__log_level)

    def __register_fully_extracted_warc_file(self, warc_path):
        """
        Saves the URL warc_url in the log file for fully extracted WARC URLs
        :param warc_url:
        :return:
        """
        if self.__log_pathname_fully_extracted_warcs is not None:
            with open(self.__log_pathname_fully_extracted_warcs, 'a') as log_file:
                log_file.write(warc_path + '\n')

    def filter_record(self, warc_record, article=None):
        """
        Returns true if a record passes all tests: hosts, publishing date
        :param warc_record:
        :return: A tuple of (True or False) and an article (might be None)
        """
        # filter by host
        if self.__filter_valid_hosts:
            url = warc_record.rec_headers.get_header('WARC-Target-URI')

            # very simple check, check if one of the required host names is contained in the url of the WARC transaction
            # better would be to extract the host name from the WARC transaction Target URI and then check for equality
            # because currently something like g.co?forward_url=facebook.com would yield a positive filter test for
            # facebook.com even though the actual host is g.co
            for valid_host in self.__filter_valid_hosts:
                if valid_host in url:
                    break
            else:
                return False, article

        # filter by date
        if self.__filter_start_date or self.__filter_end_date:
            if not article:
                article = self._from_warc(warc_record)

            publishing_date = self.__get_publishing_date(warc_record, article)
            if not publishing_date:
                if self.__filter_strict_date:
                    return False, article
            else:  # here we for sure have a date
                # is article published too early?
                if self.__filter_start_date and publishing_date < self.__filter_start_date:
                    return False, article
                if self.__filter_end_date and publishing_date > self.__filter_end_date:
                    return False, article

        return True, article

    def __get_publishing_date(self, warc_record, article):
        """
        Extracts the publishing date from the record
        :param warc_record:
        :return:
        """
        if hasattr(article, 'date_publish'):
            return parser.parse(article.date_publish) if isinstance(article.date_publish, str) else article.date_publish
        else:
            return None

    def __get_remote_index(self):
        """
        Gets the index of news crawl files from commoncrawl.org and returns an array of names
        :return:
        """
        return commoncrawl_crawler.__get_remote_index()

    def __on_download_progress_update(self, blocknum, blocksize, totalsize):
        """
        Prints some download progress information
        :param blocknum:
        :param blocksize:
        :param totalsize:
        :return:
        """
        if not self.__show_download_progress:
            return

        readsofar = blocknum * blocksize
        if totalsize > 0:
            s = "\r%s / %s" % (size(readsofar), size(totalsize))
            sys.stdout.write(s)
            if readsofar >= totalsize:  # near the end
                sys.stderr.write("\r")
        else:  # total size is unknown
            sys.stdout.write("\rread %s" % (size(readsofar)))

    def __download(self, path):
        """
        Download and save a file locally.
        :param url: Where to download from
        :return: File path name of the downloaded file
        """
        local_filename = urllib.parse.quote_plus(path)
        local_filepath = os.path.join(self.__local_download_dir_warc, local_filename)

        if os.path.isfile(local_filepath) and self.__reuse_previously_downloaded_files:
            self.__logger.info("found local file %s, not downloading again due to configuration", local_filepath)
            return local_filepath
        else:
            # cleanup
            try:
                os.remove(local_filepath)
            except OSError:
                pass

            # download
            if self.__s3_client:
                with open(local_filepath, 'wb') as file_obj:
                    self.__s3_client.download_fileobj(self.__cc_bucket, path, file_obj)
                return local_filepath
            else:
                url = self.__cc_base_url + path
                self.__logger.info('downloading %s (local: %s)', url, local_filepath)
                urllib.request.urlretrieve(url, local_filepath, reporthook=self.__on_download_progress_update)
                self.__logger.info('download completed, local file: %s', local_filepath)
                return local_filepath

    def _from_warc(self, record):
        return NewsPlease.from_warc(record, decode_errors="replace" if self.__ignore_unicode_errors else "strict", fetch_images=self.__fetch_images)

    def __process_warc_gz_file(self, path_name):
        """
        Iterates all transactions in one WARC file and for each transaction tries to extract an article object.
        Afterwards, each article is checked against the filter criteria and if all are passed, the function
        on_valid_article_extracted is invoked with the article object.
        :param path_name:
        :return:
        """
        counter_article_total = 0
        counter_article_passed = 0
        counter_article_discarded = 0
        counter_article_error = 0
        start_time = time.time()

        with open(path_name, 'rb') as stream:
            for record in ArchiveIterator(stream):
                try:
                    if record.rec_type == 'response':
                        counter_article_total += 1

                        # if the article passes filter tests, we notify the user
                        try:
                            filter_pass, article = self.filter_record(record)
                        except (UnicodeDecodeError, EmptyResponseError):
                            filter_pass = False
                        if filter_pass:
                            try:
                                if not article:
                                    article = self._from_warc(record)
                            except (UnicodeDecodeError, EmptyResponseError):
                                filter_pass = False
                        if filter_pass:
                            counter_article_passed += 1

                            self.__logger.info('article pass (%s; %s; %s)', article.source_domain, article.date_publish,
                                               article.title)
                            self.__callback_on_article_extracted(article)
                        else:
                            counter_article_discarded += 1

                            if article:
                                self.__logger.info('article discard (%s; %s; %s)', article.source_domain,
                                                   article.date_publish,
                                                   article.title)
                            else:
                                self.__logger.info('article discard (%s)',
                                                   record.rec_headers.get_header('WARC-Target-URI'))

                        if counter_article_total % 10 == 0:
                            elapsed_secs = time.time() - start_time
                            secs_per_article = elapsed_secs / counter_article_total
                            self.__logger.info('statistics')
                            self.__logger.info('pass = %i, discard = %i, error = %i, total = %i',
                                               counter_article_passed,
                                               counter_article_discarded, counter_article_error, counter_article_total)
                            self.__logger.info('extraction from current WARC file started %s; %f s/article',
                                               human(start_time), secs_per_article)
                except:
                    if self.__continue_after_error:
                        self.__logger.error('Unexpected error: %s (%s)', *sys.exc_info()[0:2])
                        self.__logger.error(sys.exc_info()[2], exc_info=True)
                        counter_article_error += 1
                        pass
                    else:
                        raise

        # cleanup
        if self.__delete_warc_after_extraction:
            os.remove(path_name)

        self.__register_fully_extracted_warc_file(self.__warc_path)
        self.__callback_on_warc_completed(self.__warc_path, counter_article_passed, counter_article_discarded,
                                          counter_article_error, counter_article_total)

    def __run(self):
        """
        Main execution method, which consists of: get an up-to-date list of WARC files, and for each of them: download
        and extract articles. Each article is checked against a filter. Finally, for each valid article the method
        on_valid_article_extracted will be invoked after the extraction of the article has completed.
        :return:
        """
        self.__setup()

        local_path_name = self.__download(self.__warc_path)
        self.__process_warc_gz_file(local_path_name)

    def extract_from_commoncrawl(self, warc_path, callback_on_article_extracted,
                                 callback_on_warc_completed=None,
                                 valid_hosts=None,
                                 start_date=None, end_date=None,
                                 strict_date=True, reuse_previously_downloaded_files=True, local_download_dir_warc=None,
                                 continue_after_error=True, ignore_unicode_errors=False,
                                 show_download_progress=False, log_level=logging.ERROR, delete_warc_after_extraction=True,
                                 log_pathname_fully_extracted_warcs=None, fetch_images=False):
        """
        Crawl and extract articles form the news crawl provided by commoncrawl.org. For each article that was extracted
        successfully the callback function callback_on_article_extracted is invoked where the first parameter is the
        article object.
        :param log_pathname_fully_extracted_warcs:
        :param delete_warc_after_extraction:
        :param warc_path:
        :param callback_on_article_extracted:
        :param callback_on_warc_completed:
        :param valid_hosts:
        :param start_date:
        :param end_date:
        :param strict_date:
        :param reuse_previously_downloaded_files:
        :param local_download_dir_warc:
        :param continue_after_error:
        :param show_download_progress:
        :param log_level:
        :return:
        """
        self.__warc_path = warc_path
        self.__filter_valid_hosts = valid_hosts
        self.__filter_start_date = start_date
        self.__filter_end_date = end_date
        self.__filter_strict_date = strict_date
        if local_download_dir_warc:
            self.__local_download_dir_warc = local_download_dir_warc
        self.__reuse_previously_downloaded_files = reuse_previously_downloaded_files
        self.__continue_after_error = continue_after_error
        self.__ignore_unicode_errors = ignore_unicode_errors
        self.__fetch_images = fetch_images
        self.__callback_on_article_extracted = callback_on_article_extracted
        self.__callback_on_warc_completed = callback_on_warc_completed
        self.__show_download_progress = show_download_progress
        self.__log_level = log_level
        self.__delete_warc_after_extraction = delete_warc_after_extraction
        self.__log_pathname_fully_extracted_warcs = log_pathname_fully_extracted_warcs

        self.__s3_client = None
        try:
            s3_client = boto3.client('s3')
            # Verify access to commoncrawl bucket
            s3_client.head_bucket(Bucket=self.__cc_bucket)
            self.__s3_client = s3_client
        except (botocore.exceptions.ClientError, botocore.exceptions.NoCredentialsError):
            self.__logger.info('Failed to read %s bucket, using monthly WARC file listings', self.__cc_bucket)


        self.__run()
