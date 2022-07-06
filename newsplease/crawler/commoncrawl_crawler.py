#!/usr/bin/env python
"""
Provides functionality to crawl and extract news articles from commoncrawl.org. Filter criteria, such as publish date
and host list, can be defined. Currently, all WARC files will be downloaded to the path WORKINGDIR/cc_download_warc, if
not otherwise specified.
"""
import logging
import os
import time
from functools import partial
from multiprocessing import Pool
import datetime
import gzip
from urllib.parse import urlparse

import boto3
import botocore
from dateutil import parser
import requests
from scrapy.utils.log import configure_logging

from ..crawler.commoncrawl_extractor import CommonCrawlExtractor

__author__ = "Felix Hamborg"
__copyright__ = "Copyright 2017"
__credits__ = ["Sebastian Nagel"]

# commoncrawl.org
__cc_base_url = 'https://data.commoncrawl.org/'
__cc_bucket = 'commoncrawl'

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

# When Common Crawl started.
__common_crawl_start_date = datetime.datetime(2016, 8, 26)

def __setup(local_download_dir_warc, log_level):
    """
    Setup
    :return:
    """
    os.makedirs(local_download_dir_warc, exist_ok=True)

    global __log_pathname_fully_extracted_warcs
    __log_pathname_fully_extracted_warcs = os.path.join(local_download_dir_warc, 'fullyextractedwarcs.list')

    # make loggers quiet
    configure_logging({"LOG_LEVEL": "ERROR"})
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.getLogger('readability').setLevel(logging.CRITICAL)
    logging.getLogger('PIL').setLevel(logging.CRITICAL)
    logging.getLogger('newspaper').setLevel(logging.CRITICAL)
    logging.getLogger('newsplease').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    logging.getLogger('jieba').setLevel(logging.CRITICAL)

    boto3.set_stream_logger('botocore', log_level)
    boto3.set_stream_logger('boto3', log_level)

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


def __iterate_by_month(start_date=None, end_date=None, month_step=1):
    if start_date is None:
        # The starting month of Common Crawl.
        start_date = __common_crawl_start_date
    if end_date is None:
        # Until now.
        end_date = datetime.datetime.today()
    current_date = start_date
    yield current_date
    while True:
        carry, new_month = divmod(current_date.month - 1 + month_step, 12)
        new_month += 1
        current_date = current_date.replace(year=current_date.year + carry,
                                            month=new_month)
        yield current_date
        if current_date > end_date:
            break


def __extract_date_from_warc_filename(path):
    fn = os.path.basename(path)
    # Assume the filename pattern is CC-NEWS-20160911145202-00018.warc.gz
    fn = fn.replace('CC-NEWS-', '')
    dt = fn.split('-')[0]

    try:
        return datetime.datetime.strptime(dt, '%Y%m%d%H%M%S')
    except:
        # return date clearly outside the range
        return datetime.datetime(1900, 1, 1)


def __date_within_period(date, start_date=None, end_date=None):
    if start_date is None:
        # The starting month of Common Crawl.
        start_date = __common_crawl_start_date
    if end_date is None:
        # Until now.
        end_date = datetime.datetime.today()
    return start_date <= date < end_date


def __get_remote_index(warc_files_start_date=None, warc_files_end_date=None):
    """
    Gets the index of news crawl files from commoncrawl.org and returns an array of names
    :param warc_files_start_date: only list .warc files with greater or equal date in
    their filename
    :param warc_files_end_date: only list .warc files with smaller date in their filename
    :return:
    """

    s3_client = boto3.client('s3')
    # Verify access to commoncrawl bucket
    try:
        s3_client.head_bucket(Bucket=__cc_bucket)
    except (botocore.exceptions.ClientError, botocore.exceptions.NoCredentialsError):
        __logger.info('Failed to read %s bucket, using monthly WARC file listings', __cc_bucket)
        s3_client = None

    objects = []

    if s3_client:
        def s3_list_objects(bucket, prefix):
            response = s3_client.list_objects(Bucket=bucket, Prefix=prefix)
            if 'Contents' not in response:
                return []
            return [x['Key'] for x in response['Contents']]

        if warc_files_start_date or warc_files_end_date:
            # The news files are grouped per year and month in separate folders
            warc_dates = __iterate_by_month(start_date=warc_files_start_date, end_date=warc_files_end_date)
            for date in warc_dates:
                year = date.strftime('%Y')
                month = date.strftime('%m')
                prefix = 'crawl-data/CC-NEWS/%s/%s/' % (year, month)
                __logger.debug('Listing objects on S3 bucket %s and prefix %s', __cc_bucket, prefix)
                objects += s3_list_objects(__cc_bucket, prefix)
        else:
            objects = s3_list_objects(__cc_bucket, 'crawl-data/CC-NEWS/')

    else:
        # The news files are grouped per year and month in separate folders
        warc_dates = __iterate_by_month(start_date=warc_files_start_date, end_date=warc_files_end_date)
        for date in warc_dates:
            year = date.strftime('%Y')
            month = date.strftime('%m')
            url = '%scrawl-data/CC-NEWS/%s/%s/warc.paths.gz' % (__cc_base_url, year, month)
            __logger.debug('Fetching WARC paths listing %s', url)
            response = requests.get(url)
            if response:
                objects += gzip.decompress(response.content).decode('ascii').strip().split('\n')
            else:
                __logger.info('Failed to fetch WARC file list %s: %s', url, response)

    if warc_files_start_date or warc_files_end_date:
        # Now filter further on day of month, hour, minute
        objects = [
            p for p in objects if __date_within_period(
                __extract_date_from_warc_filename(p),
                start_date=warc_files_start_date,
                end_date=warc_files_end_date,
            )
        ]

    __logger.info('Found %i WARC files', len(objects))

    return objects

def __get_url_path(url_or_path):
    if url_or_path.startswith('http:') or url_or_path.startswith('https:'):
        try:
            url = urlparse(url_or_path)
            return url.path.lstrip('/') # trim leading slash
        except:
            pass
    return url_or_path

def __get_list_of_fully_extracted_warc_paths():
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

    # (back-ward compatibility) if it's a URL keep only the path
    list_warcs = [__get_url_path(x) for x in list_warcs]

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
    __logger.info("estimated remaining time [h] = %f", remaining_warcs * h_per_warc)

    # invoke the external callback
    __extern_callback_on_warc_completed(warc_path, __counter_article_passed, __counter_article_discarded,
                                        __counter_article_error, __counter_article_total, __counter_warc_processed)


def __start_commoncrawl_extractor(warc_path, callback_on_article_extracted=None,
                                  callback_on_warc_completed=None, valid_hosts=None,
                                  start_date=None, end_date=None,
                                  strict_date=True, reuse_previously_downloaded_files=True,
                                  local_download_dir_warc=None,
                                  continue_after_error=True, show_download_progress=False,
                                  log_level=logging.ERROR,
                                  delete_warc_after_extraction=True,
                                  continue_process=True,
                                  log_pathname_fully_extracted_warcs=None,
                                  extractor_cls=CommonCrawlExtractor,
                                  fetch_images=False):
    """
    Starts a single CommonCrawlExtractor
    :param warc_path: path to the WARC file on s3://commoncrawl/ resp. https://data.commoncrawl.org/
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
    :param extractor_cls: A subclass of CommonCrawlExtractor, which can be used
        to add custom filtering by overriding .filter_record(...)
    :return:
    """
    commoncrawl_extractor = extractor_cls()
    commoncrawl_extractor.extract_from_commoncrawl(warc_path, callback_on_article_extracted,
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
                                                   log_pathname_fully_extracted_warcs=__log_pathname_fully_extracted_warcs,
                                                   fetch_images=fetch_images)


def crawl_from_commoncrawl(callback_on_article_extracted, callback_on_warc_completed=None, valid_hosts=None,
                           start_date=None, end_date=None, warc_files_start_date=None, warc_files_end_date=None, strict_date=True,
                           reuse_previously_downloaded_files=True, local_download_dir_warc=None,
                           continue_after_error=True, show_download_progress=False,
                           number_of_extraction_processes=4, log_level=logging.ERROR,
                           delete_warc_after_extraction=True, continue_process=True,
                           extractor_cls=CommonCrawlExtractor, fetch_images=False,
                           dry_run=False):
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
    :param warc_files_start_date
    :param warc_files_end_date
    :param strict_date:
    :param reuse_previously_downloaded_files:
    :param local_download_dir_warc:
    :param continue_after_error:
    :param show_download_progress:
    :param log_level:
    :param extractor_cls:
    :param dry_run: if True just list the WARC files to be processed but do not actually process them
    :return:
    """
    __setup(local_download_dir_warc, log_level)

    global __extern_callback_on_warc_completed
    __extern_callback_on_warc_completed = callback_on_warc_completed

    cc_news_crawl_names = __get_remote_index(warc_files_start_date, warc_files_end_date)
    global __number_of_warc_files_on_cc
    __number_of_warc_files_on_cc = len(cc_news_crawl_names)
    __logger.info('found %i files at commoncrawl.org', __number_of_warc_files_on_cc)

    # multiprocessing (iterate the list of crawl_names, and for each: download and process it)
    __logger.info('creating extraction process pool with %i processes', number_of_extraction_processes)
    warc_paths = []
    fully_extracted_warc_paths = __get_list_of_fully_extracted_warc_paths()
    for warc_path in cc_news_crawl_names:
        if continue_process:
            # check if the current WARC has already been fully extracted (assuming that the filter criteria have not
            # been changed!)
            if warc_path in fully_extracted_warc_paths:
                __logger.info('skipping WARC because fully extracted: %s', warc_path)
                global __counter_warc_skipped
                __counter_warc_skipped += 1
                pass
            else:
                warc_paths.append(warc_path)

        else:
            # if not continue process, then always add
            warc_paths.append(warc_path)

    if dry_run:
        for warc_path in warc_paths:
            __logger.info('(Dry run) Selected WARC file for processing: %s', warc_path)

    # run the crawler in the current, single process if number of extraction processes is set to 1
    elif number_of_extraction_processes > 1:
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
                                                log_pathname_fully_extracted_warcs=__log_pathname_fully_extracted_warcs,
                                                extractor_cls=extractor_cls,
                                                fetch_images=fetch_images),
                                        warc_paths)
    else:
        for warc_path in warc_paths:
            __start_commoncrawl_extractor(warc_path,
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
                                          log_pathname_fully_extracted_warcs=__log_pathname_fully_extracted_warcs,
                                          extractor_cls=extractor_cls,
                                          fetch_images=fetch_images)
