#!/usr/bin/env python
"""
Provides functionality to crawl and extract news articles from commoncrawl.org. Filter criteria, such as publish date
and host list, can be defined. Currently, all WARC files will be downloaded to the path WORKINGDIR/cc_download_warc, if
not otherwise specified.
"""
import logging
import os
import subprocess
from functools import partial
from multiprocessing import Pool

from dateutil import parser
from scrapy.utils.log import configure_logging

from newsplease import NewsPlease
from newsplease.crawler.commoncrawl_extractor import CommonCrawlExtractor

__author__ = "Felix Hamborg"
__copyright__ = "Copyright 2017"
__credits__ = ["Sebastian Nagel"]

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
# parallelity
__number_of_extraction_processes = 4

# commoncrawl.org
__cc_base_url = 'https://commoncrawl.s3.amazonaws.com/'
__cc_news_crawl_names = None

# event handler called when an article was extracted successfully and passed all filter criteria
__callback_on_article_extracted = None
# if the download progress is shown
__show_download_progress = False
# debug: same process
__debug_same_process = False

# logging
logging.basicConfig(level=__log_level)
__logger = logging.getLogger(__name__)


def __setup():
    """
    Setup
    :return:
    """
    if not os.path.exists(__local_download_dir_warc):
        os.makedirs(__local_download_dir_warc)

    # make loggers quite
    configure_logging({"LOG_LEVEL": "ERROR"})
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.getLogger('readability').setLevel(logging.CRITICAL)
    logging.getLogger('PIL').setLevel(logging.CRITICAL)
    logging.getLogger('newspaper').setLevel(logging.CRITICAL)
    logging.getLogger('newsplease').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)

    # set own logger
    logging.basicConfig(level=__log_level)
    __logger = logging.getLogger(__name__)
    __logger.setLevel(__log_level)


def __filter_record(warc_record, article=None):
    """
    Returns true if a record passes all tests: hosts, publishing date
    :param warc_record:
    :return: A tuple of (True or False) and an article (might be None)
    """
    # filter by host
    if __filter_valid_hosts:
        url = warc_record.rec_headers.get_header('WARC-Target-URI')

        # very simple check, check if one of the required host names is contained in the url of the WARC transaction
        # better would be to extract the host name from the WARC transaction Target URI and then check for equality
        # because currently something like g.co?forward_url=facebook.com would yield a positive filter test for
        # facebook.com even though the actual host is g.co
        for valid_host in __filter_valid_hosts:
            if valid_host not in url:
                return False, article

    # filter by date
    if __filter_start_date or __filter_end_date:
        if not article:
            article = NewsPlease.from_warc(warc_record)

        publishing_date = __get_publishing_date(warc_record, article)
        if not publishing_date:
            if __filter_strict_date:
                return False, article
        else:  # here we for sure have a date
            # is article published too early?
            if __filter_start_date:
                if publishing_date < __filter_start_date:
                    return False, article
            if __filter_end_date:
                if publishing_date > __filter_end_date:
                    return False, article

    return True, article


def __get_publishing_date(warc_record, article):
    """
    Extracts the publishing date from the record
    :param warc_record:
    :return:
    """
    if article.publish_date:
        return parser.parse(article.publish_date)
    else:
        return None


def __get_download_url(name):
    """
    Creates a download url given the name
    :param name:
    :return:
    """
    return __cc_base_url + name


def __get_remote_index():
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
    __logger.info('executing: %s', cmd)
    stdout_data = subprocess.getoutput(cmd)

    lines = stdout_data.splitlines()
    return lines


def __run():
    """
    Main execution method, which consists of: get an up-to-date list of WARC files, and for each of them: download
    and extract articles. Each article is checked against a filter. Finally, for each valid article the method
    on_valid_article_extracted will be invoked after the extraction of the article has completed.
    :return:
    """
    __setup()

    __cc_news_crawl_names = __get_remote_index()
    __logger.info('found %i files at commoncrawl.org', len(__cc_news_crawl_names))

    # multiprocessing (iterate the list of crawl_names, and for each: download and process it)
    __logger.info('creating extraction process pool with %i processes', __number_of_extraction_processes)


def crawl_from_commoncrawl(callback_on_article_extracted, valid_hosts=None, start_date=None, end_date=None,
                           strict_date=True, reuse_previously_downloaded_files=True, local_download_dir_warc=None,
                           continue_after_error=True, show_download_progress=False,
                           number_of_extraction_processes=4, log_level=logging.ERROR):
    """
    Crawl and extract articles form the news crawl provided by commoncrawl.org. For each article that was extracted
    successfully the callback function callback_on_article_extracted is invoked where the first parameter is the
    article object.
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
    __filter_valid_hosts = valid_hosts
    __filter_start_date = start_date
    __filter_end_date = end_date
    __filter_strict_date = strict_date
    if local_download_dir_warc:
        __local_download_dir_warc = local_download_dir_warc
    __reuse_previously_downloaded_files = reuse_previously_downloaded_files
    __continue_after_error = continue_after_error
    __callback_on_article_extracted = callback_on_article_extracted
    __show_download_progress = show_download_progress
    __number_of_extraction_processes = number_of_extraction_processes
    __log_level = log_level

    __setup()

    __cc_news_crawl_names = __get_remote_index()
    __logger.info('found %i files at commoncrawl.org', len(__cc_news_crawl_names))

    # multiprocessing (iterate the list of crawl_names, and for each: download and process it)
    __logger.info('creating extraction process pool with %i processes', __number_of_extraction_processes)
    warc_download_urls = []
    for name in __cc_news_crawl_names:
        warc_download_url = __get_download_url(name)
        warc_download_urls.append(warc_download_url)

    if not __debug_same_process:
        with Pool(__number_of_extraction_processes) as extraction_process_pool:
            extraction_process_pool.map(partial(__start_commoncrawl_extractor,
                                                callback_on_article_extracted=__callback_on_article_extracted,
                                                valid_hosts=valid_hosts,
                                                start_date=start_date, end_date=end_date,
                                                strict_date=strict_date,
                                                reuse_previously_downloaded_files=reuse_previously_downloaded_files,
                                                local_download_dir_warc=local_download_dir_warc,
                                                continue_after_error=continue_after_error,
                                                show_download_progress=show_download_progress,
                                                log_level=log_level),
                                        warc_download_urls)
    else:
        for warc_download_url in warc_download_urls:
            __start_commoncrawl_extractor(warc_download_url,
                                          callback_on_article_extracted=__callback_on_article_extracted,
                                          valid_hosts=valid_hosts,
                                          start_date=start_date, end_date=end_date,
                                          strict_date=strict_date,
                                          reuse_previously_downloaded_files=reuse_previously_downloaded_files,
                                          local_download_dir_warc=local_download_dir_warc,
                                          continue_after_error=continue_after_error,
                                          show_download_progress=show_download_progress,
                                          log_level=log_level)


def __start_commoncrawl_extractor(warc_download_url, callback_on_article_extracted=None, valid_hosts=None,
                                  start_date=None, end_date=None,
                                  strict_date=True, reuse_previously_downloaded_files=True,
                                  local_download_dir_warc=None,
                                  continue_after_error=True, show_download_progress=False,
                                  log_level=logging.ERROR):
    """
    Starts a single CommonCrawlExtractor
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
    :param number_of_extraction_processes:
    :param log_level:
    :return:
    """
    commoncrawl_extractor = CommonCrawlExtractor()
    commoncrawl_extractor.extract_from_commoncrawl(warc_download_url, callback_on_article_extracted,
                                                   valid_hosts=valid_hosts,
                                                   start_date=start_date, end_date=end_date,
                                                   strict_date=strict_date,
                                                   reuse_previously_downloaded_files=reuse_previously_downloaded_files,
                                                   local_download_dir_warc=local_download_dir_warc,
                                                   continue_after_error=continue_after_error,
                                                   show_download_progress=show_download_progress,
                                                   log_level=log_level)
