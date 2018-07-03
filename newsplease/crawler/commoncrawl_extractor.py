#!/usr/bin/env python
"""
Provides functionality to crawl and extract news articles from a single WARC file from commoncrawl.org. Filter criteria, such as publish date
and host list, can be defined. Currently, the WARC file will be downloaded to the path WORKINGDIR/cc_download_warc, if
not otherwise specified.
"""
import logging
import os
import subprocess
import sys
import time

from ago import human
from dateutil import parser
from hurry.filesize import size
from scrapy.utils.log import configure_logging
from six.moves import urllib
from warcio.archiveiterator import ArchiveIterator

from .. import NewsPlease

__author__ = "Felix Hamborg"
__copyright__ = "Copyright 2017"
__credits__ = ["Sebastian Nagel"]


class CommonCrawlExtractor:
    # remote url where we can download the warc file
    __warc_download_url = None
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
    # log level
    __log_level = logging.INFO
    __delete_warc_after_extraction = True
    ____log_pathname_fully_extracted_warcs = None

    # commoncrawl.org
    __cc_base_url = 'https://commoncrawl.s3.amazonaws.com/'
    __cc_news_crawl_names = None

    # event handler called when an article was extracted successfully and passed all filter criteria
    __callback_on_article_extracted = None
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
        if not os.path.exists(self.__local_download_dir_warc):
            os.makedirs(self.__local_download_dir_warc)

        # make loggers quite
        configure_logging({"LOG_LEVEL": "ERROR"})
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.getLogger('readability').setLevel(logging.CRITICAL)
        logging.getLogger('PIL').setLevel(logging.CRITICAL)
        logging.getLogger('newspaper').setLevel(logging.CRITICAL)
        logging.getLogger('newsplease').setLevel(logging.CRITICAL)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)

        # set own logger
        logging.basicConfig(level=self.__log_level)
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(self.__log_level)

    def __register_fully_extracted_warc_file(self, warc_url):
        """
        Saves the URL warc_url in the log file for fully extracted WARC URLs
        :param warc_url:
        :return:
        """
        with open(self.__log_pathname_fully_extracted_warcs, 'a') as log_file:
            log_file.write(warc_url + '\n')

    def __filter_record(self, warc_record, article=None):
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
                article = NewsPlease.from_warc(warc_record)

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
        if 'publish_date' in article:
            return parser.parse(article.publish_date)
        else:
            return None

    def __get_download_url(self, name):
        """
        Creates a download url given the name
        :param name:
        :return:
        """
        return self.__cc_base_url + name

    def __get_remote_index(self):
        """
        Gets the index of news crawl files from commoncrawl.org and returns an array of names
        :return:
        """
        # cleanup
        subprocess.getoutput("rm tmpaws.txt")
        # get the remote info
        cmd = "aws s3 ls --recursive s3://commoncrawl/crawl-data/CC-NEWS/ --no-sign-request > tmpaws.txt && " \
              "awk '{ print $4 }' tmpaws.txt && " \
              "rm tmpaws.txt"
        self.__logger.info('executing: %s', cmd)
        stdout_data = subprocess.getoutput(cmd)
        print(stdout_data)

        lines = stdout_data.splitlines()
        return lines

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

    def __download(self, url):
        """
        Download and save a file locally.
        :param url: Where to download from
        :return: File path name of the downloaded file
        """
        local_filename = urllib.parse.quote_plus(url)
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
            self.__logger.info('downloading %s (local: %s)', url, local_filepath)
            urllib.request.urlretrieve(url, local_filepath, reporthook=self.__on_download_progress_update)
            self.__logger.info('download completed, local file: %s', local_filepath)
            return local_filepath

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
        start_time = time.time()

        with open(path_name, 'rb') as stream:
            for record in ArchiveIterator(stream):
                # try:
                if record.rec_type == 'response':
                    counter_article_total += 1

                    # if the article passes filter tests, we notify the user
                    filter_pass, article = self.__filter_record(record)
                    if filter_pass:
                        counter_article_passed += 1

                        if not article:
                            article = NewsPlease.from_warc(record)

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
                        self.__logger.info('pass = %i, discard = %i, total = %i', counter_article_passed,
                                           counter_article_discarded, counter_article_total)
                        self.__logger.info('extraction from current WARC file started %s; %f s/article',
                                           human(start_time), secs_per_article)
                        # except:
                        #    if self.__continue_after_error:
                        #        self.__logger.error('Unexpected error: %s', sys.exc_info()[0])
                        #        pass
                        #    else:
                        #        raise

        # cleanup
        if self.__delete_warc_after_extraction:
            os.remove(path_name)

        self.__register_fully_extracted_warc_file(self.__warc_download_url)

    def __run(self):
        """
        Main execution method, which consists of: get an up-to-date list of WARC files, and for each of them: download
        and extract articles. Each article is checked against a filter. Finally, for each valid article the method
        on_valid_article_extracted will be invoked after the extraction of the article has completed.
        :return:
        """
        self.__setup()

        local_path_name = self.__download(self.__warc_download_url)
        self.__process_warc_gz_file(local_path_name)

    def extract_from_commoncrawl(self, warc_download_url, callback_on_article_extracted, valid_hosts=None,
                                 start_date=None, end_date=None,
                                 strict_date=True, reuse_previously_downloaded_files=True, local_download_dir_warc=None,
                                 continue_after_error=True, show_download_progress=False,
                                 log_level=logging.ERROR, delete_warc_after_extraction=True,
                                 log_pathname_fully_extracted_warcs=None):
        """
        Crawl and extract articles form the news crawl provided by commoncrawl.org. For each article that was extracted
        successfully the callback function callback_on_article_extracted is invoked where the first parameter is the
        article object.
        :param log_pathname_fully_extracted_warcs:
        :param delete_warc_after_extraction:
        :param warc_download_url:
        :param callback_on_article_extracted:
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
        self.__warc_download_url = warc_download_url
        self.__filter_valid_hosts = valid_hosts
        self.__filter_start_date = start_date
        self.__filter_end_date = end_date
        self.__filter_strict_date = strict_date
        if local_download_dir_warc:
            self.__local_download_dir_warc = local_download_dir_warc
        self.__reuse_previously_downloaded_files = reuse_previously_downloaded_files
        self.__continue_after_error = continue_after_error
        self.__callback_on_article_extracted = callback_on_article_extracted
        self.__show_download_progress = show_download_progress
        self.__log_level = log_level
        self.__delete_warc_after_extraction = delete_warc_after_extraction
        self.__log_pathname_fully_extracted_warcs = log_pathname_fully_extracted_warcs

        self.__run()
