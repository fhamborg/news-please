#!/usr/bin/env python
"""
This scripts downloads WARC files from commoncrawl.org's news crawl and extracts articles from these files. You can
define filter criteria that need to be met (see YOUR CONFIG section), otherwise an article is discarded. Currently, the
script stores the extracted articles in JSON files, but this behaviour can be adapted to your needs in the method
on_valid_article_extracted. To speed up the crawling and extraction process, the script supports multiprocessing. You can
control the number of processes with the parameter my_number_of_extraction_processes.

You can also crawl and extract articles programmatically, i.e., from within your own code, by using the class
CommonCrawlCrawler provided in newsplease.crawler.commoncrawl_crawler.py

In case the script crashes and contains a log message in the beginning that states that only 1 file on AWS storage
was found, make sure that awscli was correctly installed. You can check that by running aws --version from a terminal.
If aws is not installed, you can (on Ubuntu) also install it using sudo apt-get install awscli.

This script uses relative imports to ensure that the latest, local version of news-please is used, instead of the one
that might have been installed with pip. Hence, you must run this script following this workflow.
git clone https://github.com/fhamborg/news-please.git
cd news-please
python3 -m newsplease.examples.commoncrawl
"""
import hashlib
import json
import logging
import os
import sys

from ..crawler import commoncrawl_crawler as commoncrawl_crawler

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
# end date (if None, any date is OK as end date), as datetime
my_filter_end_date = None  # datetime.datetime(2016, 12, 31)
# if date filtering is strict and news-please could not detect the date of an article, the article will be discarded
my_filter_strict_date = True
# if True, the script checks whether a file has been downloaded already and uses that file instead of downloading
# again. Note that there is no check whether the file has been downloaded completely or is valid!
my_reuse_previously_downloaded_files = True
# continue after error
my_continue_after_error = True
# show the progress of downloading the WARC files
my_show_download_progress = False
# log_level
my_log_level = logging.INFO
# json export style
my_json_export_style = 1  # 0 (minimize), 1 (pretty)
# number of extraction processes
my_number_of_extraction_processes = 1
# if True, the WARC file will be deleted after all articles have been extracted from it
my_delete_warc_after_extraction = True
# if True, will continue extraction from the latest fully downloaded but not fully extracted WARC files and then
# crawling new WARC files. This assumes that the filter criteria have not been changed since the previous run!
my_continue_process = True
############ END YOUR CONFIG #########


# logging
logging.basicConfig(level=my_log_level)
__logger = logging.getLogger(__name__)


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
    final_path = os.path.join(path, sub_dir)
    if not os.path.exists(final_path):
        os.makedirs(final_path)
    return os.path.join(final_path, short_filename + '.json')


def on_valid_article_extracted(article):
    """
    This function will be invoked for each article that was extracted successfully from the archived data and that
    satisfies the filter criteria.
    :param article:
    :return:
    """
    # do whatever you need to do with the article (e.g., save it to disk, store it in ElasticSearch, etc.)
    with open(__get_pretty_filepath(my_local_download_dir_article, article), 'w', encoding='utf-8') as outfile:
        if my_json_export_style == 0:
            json.dump(article.__dict__, outfile, default=str, separators=(',', ':'), ensure_ascii=False)
        elif my_json_export_style == 1:
            json.dump(article.__dict__, outfile, default=str, indent=4, sort_keys=True, ensure_ascii=False)
        # ...


def callback_on_warc_completed(warc_path, counter_article_passed, counter_article_discarded,
                               counter_article_error, counter_article_total, counter_warc_processed):
    """
    This function will be invoked for each WARC file that was processed completely. Parameters represent total values,
    i.e., cumulated over all all previously processed WARC files.
    :param warc_path:
    :param counter_article_passed:
    :param counter_article_discarded:
    :param counter_article_error:
    :param counter_article_total:
    :param counter_warc_processed:
    :return:
    """
    pass


def main():
    global my_local_download_dir_warc
    global my_local_download_dir_article
    delete_warc_after_extraction = False
    global my_number_of_extraction_processes

    if len(sys.argv) >= 2:
        my_local_download_dir_warc = sys.argv[1]
    if len(sys.argv) >= 3:
        my_local_download_dir_article = sys.argv[2]
    if len(sys.argv) >= 4:
        delete_warc_after_extraction = sys.argv[3] == "delete"
    if len(sys.argv) >= 5:
        my_number_of_extraction_processes = int(sys.argv[4])

    print("my_local_download_dir_warc=" + my_local_download_dir_warc)
    print("my_local_download_dir_article=" + my_local_download_dir_article)
    print("delete_warc_after_extraction=" + str(delete_warc_after_extraction))
    print("my_number_of_extraction_processes=" + str(my_number_of_extraction_processes))

    __setup__()
    commoncrawl_crawler.crawl_from_commoncrawl(on_valid_article_extracted,
                                               callback_on_warc_completed=callback_on_warc_completed,
                                               valid_hosts=my_filter_valid_hosts,
                                               start_date=my_filter_start_date,
                                               end_date=my_filter_end_date,
                                               strict_date=my_filter_strict_date,
                                               reuse_previously_downloaded_files=my_reuse_previously_downloaded_files,
                                               local_download_dir_warc=my_local_download_dir_warc,
                                               continue_after_error=my_continue_after_error,
                                               show_download_progress=my_show_download_progress,
                                               number_of_extraction_processes=my_number_of_extraction_processes,
                                               log_level=my_log_level,
                                               delete_warc_after_extraction=delete_warc_after_extraction,
                                               continue_process=True)


if __name__ == "__main__":
    main()
