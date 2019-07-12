#!/usr/bin/env python
"""
Provides functionality to crawl and extract news articles from commoncrawl.org. Filter criteria, such as publish date
and host list, can be defined. Currently, all WARC files will be downloaded to the path WORKINGDIR/cc_download_warc, if
not otherwise specified.
"""
import logging
import os
import subprocess
import time
from functools import partial
from multiprocessing import Pool

from dateutil import parser
from scrapy.utils.log import configure_logging

from ..crawler.commoncrawl_extractor import CommonCrawlExtractor

__author__ = "Felix Hamborg"
__copyright__ = "Copyright 2017"
__credits__ = ["Sebastian Nagel"]

# commoncrawl.org
__cc_base_url = 'https://commoncrawl.s3.amazonaws.com/'

# log file of fully extracted WARC files
__log_pathname_fully_extracted_warcs = None

# logging
logging.basicConfig(level=logging.INFO)
__logger = logging.getLogger(__name__)

__number_of_warc_files_on_cc = 0

__extern_callback_on_warc_completed = None
__counter_article_passed = 0
__counter_article_discarded = 0
__counter_article_error = 0
__counter_article_total = 0
__counter_warc_skipped = 0
__counter_warc_processed = 0
__start_time = time.time()


def __setup(local_download_dir_warc, log_level):
    """
    Setup
    :return:
    """
    if not os.path.exists(local_download_dir_warc):
        os.makedirs(local_download_dir_warc)

    global __log_pathname_fully_extracted_warcs
    __log_pathname_fully_extracted_warcs = os.path.join(local_download_dir_warc, 'fullyextractedwarcs.list')

    # make loggers quite
    configure_logging({"LOG_LEVEL": "ERROR"})
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.getLogger('readability').setLevel(logging.CRITICAL)
    logging.getLogger('PIL').setLevel(logging.CRITICAL)
    logging.getLogger('newspaper').setLevel(logging.CRITICAL)
    logging.getLogger('newsplease').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    logging.getLogger('jieba').setLevel(logging.CRITICAL)

    # set own logger
    logging.basicConfig(level=log_level)
    __logger = logging.getLogger(__name__)
    __logger.setLevel(log_level)


def __get_publishing_date(warc_record, article):
    """
    Extracts the publishing date from the article
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
    cmd = "aws s3 ls --recursive s3://commoncrawl/crawl-data/CC-NEWS/ --no-sign-request > .tmpaws.txt && " \
          "awk '{ print $4 }' .tmpaws.txt && " \
          "rm .tmpaws.txt"
    __logger.info('executing: %s', cmd)
    stdout_data = subprocess.getoutput(cmd)

    lines = stdout_data.splitlines()
    return lines


def __get_list_of_fully_extracted_warc_urls():
    """
    Reads in the log file that contains a list of all previously, fully extracted WARC urls
    :return:
    """
    if not os.path.isfile(__log_pathname_fully_extracted_warcs):
        return []

    with open(__log_pathname_fully_extracted_warcs) as log_file:
        list_warcs = log_file.readlines()
    # remove break lines
    list_warcs = [x.strip() for x in list_warcs]

    return list_warcs


def __callback_on_warc_completed(warc_path, counter_article_passed, counter_article_discarded, counter_article_error,
                                 counter_article_total):
    """
    Internal callback on completion of one WARC file. Calculating some statistics on processing speed.
    :param warc_path:
    :param counter_article_passed:
    :param counter_article_discarded:
    :param counter_article_error:
    :param counter_article_total:
    :return:
    """
    # have to use the global keyword in order to assign a value to a global variable (see https://stackoverflow.com/a/9936482)
    global __counter_article_passed
    global __counter_article_discarded
    global __counter_article_error
    global __counter_article_total
    global __counter_warc_processed
    # global __counter_warc_skipped

    elapsed_secs = time.time() - __start_time

    __counter_article_discarded += counter_article_discarded
    __counter_article_error += counter_article_error
    __counter_article_passed += counter_article_passed
    __counter_article_total += counter_article_total
    __counter_warc_processed += 1

    sec_per_article = elapsed_secs / counter_article_total
    h_per_warc = elapsed_secs / __counter_warc_processed / 3600
    remaining_warcs = __number_of_warc_files_on_cc - (__counter_warc_processed + __counter_warc_skipped)

    __logger.info("warc processing statistics")
    __logger.info("warc files skipped = %i, processed = %i, remaining = %i, total = %i", __counter_warc_skipped,
                  __counter_warc_processed, remaining_warcs, __number_of_warc_files_on_cc)
    __logger.info("global [s/article] = %f", sec_per_article)
    __logger.info("global [h/warc] = %.3f", h_per_warc)
    __logger.info("estimated remaining time [h] = %f", remaining_warcs / h_per_warc)

    # invoke the external callback
    __extern_callback_on_warc_completed(warc_path, __counter_article_passed, __counter_article_discarded,
                                        __counter_article_error, __counter_article_total, __counter_warc_processed)


def __start_commoncrawl_extractor(warc_download_url, callback_on_article_extracted=None,
                                  callback_on_warc_completed=None, valid_hosts=None,
                                  start_date=None, end_date=None,
                                  strict_date=True, reuse_previously_downloaded_files=True,
                                  local_download_dir_warc=None,
                                  continue_after_error=True, show_download_progress=False,
                                  log_level=logging.ERROR,
                                  delete_warc_after_extraction=True,
                                  continue_process=True,
                                  log_pathname_fully_extracted_warcs=None):
    """
    Starts a single CommonCrawlExtractor
    :param warc_download_url:
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
    commoncrawl_extractor = CommonCrawlExtractor()
    commoncrawl_extractor.extract_from_commoncrawl(warc_download_url, callback_on_article_extracted,
                                                   callback_on_warc_completed=callback_on_warc_completed,
                                                   valid_hosts=valid_hosts,
                                                   start_date=start_date, end_date=end_date,
                                                   strict_date=strict_date,
                                                   reuse_previously_downloaded_files=reuse_previously_downloaded_files,
                                                   local_download_dir_warc=local_download_dir_warc,
                                                   continue_after_error=continue_after_error,
                                                   show_download_progress=show_download_progress,
                                                   log_level=log_level,
                                                   delete_warc_after_extraction=delete_warc_after_extraction,
                                                   log_pathname_fully_extracted_warcs=__log_pathname_fully_extracted_warcs)


def crawl_from_commoncrawl(callback_on_article_extracted, callback_on_warc_completed=None, valid_hosts=None,
                           start_date=None, end_date=None, strict_date=True, reuse_previously_downloaded_files=True,
                           local_download_dir_warc=None, continue_after_error=True, show_download_progress=False,
                           number_of_extraction_processes=4, log_level=logging.ERROR,
                           delete_warc_after_extraction=True, continue_process=True):
    """
    Crawl and extract articles form the news crawl provided by commoncrawl.org. For each article that was extracted
    successfully the callback function callback_on_article_extracted is invoked where the first parameter is the
    article object.
    :param continue_process:
    :param delete_warc_after_extraction:
    :param number_of_extraction_processes:
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
    __setup(local_download_dir_warc, log_level)

    global __extern_callback_on_warc_completed
    __extern_callback_on_warc_completed = callback_on_warc_completed

    cc_news_crawl_names = __get_remote_index()
    global __number_of_warc_files_on_cc
    __number_of_warc_files_on_cc = len(cc_news_crawl_names)
    __logger.info('found %i files at commoncrawl.org', __number_of_warc_files_on_cc)

    # multiprocessing (iterate the list of crawl_names, and for each: download and process it)
    __logger.info('creating extraction process pool with %i processes', number_of_extraction_processes)
    warc_download_urls = []
    fully_extracted_warc_urls = __get_list_of_fully_extracted_warc_urls()
    for name in cc_news_crawl_names:
        warc_download_url = __get_download_url(name)
        if continue_process:
            # check if the current WARC has already been fully extracted (assuming that the filter criteria have not
            # been changed!)
            if warc_download_url in fully_extracted_warc_urls:
                __logger.info('skipping WARC because fully extracted: %s' % warc_download_url)
                global __counter_warc_skipped
                __counter_warc_skipped += 1
                pass
            else:
                warc_download_urls.append(warc_download_url)

        else:
            # if not continue process, then always add
            warc_download_urls.append(warc_download_url)

    # run the crawler in the current, single process if number of extraction processes is set to 1
    if number_of_extraction_processes > 1:
        with Pool(number_of_extraction_processes) as extraction_process_pool:
            extraction_process_pool.map(partial(__start_commoncrawl_extractor,
                                                callback_on_article_extracted=callback_on_article_extracted,
                                                callback_on_warc_completed=__callback_on_warc_completed,
                                                valid_hosts=valid_hosts,
                                                start_date=start_date, end_date=end_date,
                                                strict_date=strict_date,
                                                reuse_previously_downloaded_files=reuse_previously_downloaded_files,
                                                local_download_dir_warc=local_download_dir_warc,
                                                continue_after_error=continue_after_error,
                                                show_download_progress=show_download_progress,
                                                log_level=log_level,
                                                delete_warc_after_extraction=delete_warc_after_extraction,
                                                log_pathname_fully_extracted_warcs=__log_pathname_fully_extracted_warcs),
                                        warc_download_urls)
    else:
        for warc_download_url in warc_download_urls:
            __start_commoncrawl_extractor(warc_download_url,
                                          callback_on_article_extracted=callback_on_article_extracted,
                                          callback_on_warc_completed=__callback_on_warc_completed,
                                          valid_hosts=valid_hosts,
                                          start_date=start_date, end_date=end_date,
                                          strict_date=strict_date,
                                          reuse_previously_downloaded_files=reuse_previously_downloaded_files,
                                          local_download_dir_warc=local_download_dir_warc,
                                          continue_after_error=continue_after_error,
                                          show_download_progress=show_download_progress,
                                          log_level=log_level,
                                          delete_warc_after_extraction=delete_warc_after_extraction,
                                          log_pathname_fully_extracted_warcs=__log_pathname_fully_extracted_warcs)
