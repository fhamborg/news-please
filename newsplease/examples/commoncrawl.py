#!/usr/bin/env python
"""
This scripts downloads WARC files from commoncrawl.org's news crawl and extracts articles from these files. You can
define filter criteria that need to be met (see YOUR CONFIG section), otherwise an article is discarded. Currently, the
script stores the extracted articles in JSON files, but this behaviour can be adapted to your needs in the method
on_valid_article_extracted.

You can also crawl and extract articles programmatically, i.e., from within your own code, by using the class
CommonCrawlCrawler provided in newsplease.crawler.commoncrawl_crawler.py
"""
import hashlib
import json
import logging
import os

from newsplease.crawler.commoncrawl_crawler import CommonCrawlCrawler

__author__ = "Felix Hamborg"
__copyright__ = "Copyright 2017"
__credits__ = ["Sebastian Nagel"]

############ YOUR CONFIG ############
# download dir for warc files
my_local_download_dir_warc = './cc_download_warc/'
# download dir for articles
my_local_download_dir_article = './cc_download_articles/'
# hosts (if None or empty list, any host is OK)
my_filter_valid_hosts = []  # example: ['elrancaguino.cl']
# start date (if None, any date is OK as start date), as datetime
my_filter_start_date = None  # datetime.datetime(2016, 1, 1)
# end date (if None, any date is OK as end date)
my_filter_end_date = None  # datetime.datetime(2016, 12, 31)
# if date filtering is string, e.g., if we could not detect the date of an article, we will discard the article
my_filter_strict_date = True
# if True, the script checks whether a file has been downloaded already and uses that file instead of downloading
# again. Note that there is no check whether the file has been downloaded completely or is valid!
my_reuse_previously_downloaded_files = True
# continue after error
my_continue_after_error = True
# show the progress of downloading the WARC files
my_show_download_progress = True
# log_level
my_log_level = logging.INFO
# json export style
my_json_export_style = 1  # 0 (minimize), 1 (pretty)
############ END YOUR CONFIG #########


def __setup__():
    """
    Setup
    :return:
    """
    if not os.path.exists(my_local_download_dir_article):
        os.makedirs(my_local_download_dir_article)


def __get_pretty_filepath(path, article):
    """
    Pretty might be an euphemism, but this function tries to avoid too long filenames, while keeping some structure.
    :param path:
    :param name:
    :return:
    """
    short_filename = hashlib.sha256(article.filename.encode()).hexdigest()
    sub_dir = article.source_domain
    final_path = path + sub_dir + '/'
    if not os.path.exists(final_path):
        os.makedirs(final_path)
    return final_path + short_filename + '.json'


def on_valid_article_extracted(article):
    """
    This function will be invoked for each article that was extracted successfully from the archived data and that
    satisfies the filter criteria.
    :param article:
    :return:
    """
    # do whatever you need to do with the article (e.g., save it to disk, store it in ElasticSearch, etc.)
    with open(__get_pretty_filepath(my_local_download_dir_article, article), 'w') as outfile:
        if my_json_export_style == 0:
            json.dump(article, outfile, separators=(',', ':'))
        elif my_json_export_style == 1:
            json.dump(article, outfile, indent=4, sort_keys=True)
        # ...


if __name__ == '__main__':
    __setup__()
    commoncrawl_crawler = CommonCrawlCrawler()
    commoncrawl_crawler.crawl_from_commoncrawl(on_valid_article_extracted,
                                               valid_hosts=my_filter_valid_hosts,
                                               start_date=my_filter_start_date, end_date=my_filter_end_date,
                                               strict_date=my_filter_strict_date,
                                               reuse_previously_downloaded_files=my_reuse_previously_downloaded_files,
                                               local_download_dir_warc=my_local_download_dir_warc,
                                               continue_after_error=my_continue_after_error,
                                               show_download_progress=my_show_download_progress,
                                               log_level=my_log_level)
