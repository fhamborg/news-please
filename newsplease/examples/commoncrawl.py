#!/usr/bin/env python
"""
This scripts downloads WARC files from commoncrawl.org's news crawl and extracts articles from these files. Users can
define filter criteria that need to be met (see YOUR CONFIG section), otherwise an article is discarded. Currently, the
script stores the extracted articles in JSON files, but this behaviour can be adapted to your needs in the method
on_valid_article_extracted.
"""
import datetime
import hashlib
import json
import logging
import subprocess
import sys
import time
import urllib
from urllib.request import urlretrieve

import os
from ago import human
from dateutil import parser
from hurry.filesize import size
from scrapy.utils.log import configure_logging
from warcio.archiveiterator import ArchiveIterator

from newsplease import NewsPlease

__author__ = "Felix Hamborg"
__copyright__ = "Copyright 2017"
__credits__ = ["Sebastian Nagel"]

class CommonCrawl:
    ############ YOUR CONFIG ############
    # download dir for warc files
    local_download_dir_warc = './cc_download_warc/'
    # download dir for articles
    local_download_dir_article = './cc_download_articles/'
    # hosts (if None or empty list, any host is OK)
    filter_valid_hosts = []  # example: ['elrancaguino.cl']
    # start date (if None, any date is OK as start date), as datetime
    filter_start_date = datetime.datetime(2016, 1, 1)
    # end date (if None, any date is OK as end date)
    filter_end_date = datetime.datetime(2016, 12, 31)
    # if date filtering is string, e.g., if we could not detect the date of an article, we will discard the article
    filter_strict_date = True
    # if True, the script checks whether a file has been downloaded already and uses that file instead of downloading
    # again. Note that there is no check whether the file has been downloaded completely or is valid!
    reuse_previously_downloaded_files = True
    ############ END YOUR CONFIG #########

    # commoncrawl.org
    cc_base_url = 'https://commoncrawl.s3.amazonaws.com/'
    cc_news_crawl_names = None

    # logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def __setup__(self):
        """
        Setup
        :return:
        """
        if not os.path.exists(self.local_download_dir_warc):
            os.makedirs(self.local_download_dir_warc)
        if not os.path.exists(self.local_download_dir_article):
            os.makedirs(self.local_download_dir_article)

        # make loggers quite
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.getLogger('readability').setLevel(logging.CRITICAL)
        logging.getLogger('PIL').setLevel(logging.CRITICAL)
        logging.getLogger('newspaper').setLevel(logging.CRITICAL)
        logging.getLogger('newsplease').setLevel(logging.CRITICAL)

    def __filter_record(self, warc_record, article=None):
        """
        Returns true if a record passes all tests: hosts, publishing date
        :param warc_record:
        :return: A tuple of (True or False) and an article (might be None)
        """
        # filter by host
        if self.filter_valid_hosts:
            url = warc_record.rec_headers.get_header('WARC-Target-URI')

            # very simple check, check if one of the required host names is contained in the url of the WARC transaction
            # better would be to extract the host name from the WARC transaction Target URI and then check for equality
            # because currently something like g.co?forward_url=facebook.com would yield a positive filter test for
            # facebook.com even though the actual host is g.co
            for valid_host in self.filter_valid_hosts:
                if valid_host not in url:
                    return False, article

        # filter by date
        if self.filter_start_date or self.filter_end_date:
            if not article:
                article = NewsPlease.from_warc(warc_record)

            publishing_date = self.__get_publishing_date(warc_record, article)
            if not publishing_date:
                if self.filter_strict_date:
                    return False, article
            else:  # here we for sure have a date
                # is article published too early?
                if self.filter_start_date:
                    if publishing_date < self.filter_start_date:
                        return False, article
                if self.filter_end_date:
                    if publishing_date > self.filter_end_date:
                        return False, article

        return True, article

    def __get_publishing_date(self, warc_record, article):
        """
        Extracts the publishing date from the record
        :param warc_record:
        :return:
        """
        if article.publish_date:
            return parser.parse(article.publish_date)
        else:
            return None

    def __get_download_url(self, name):
        """
        Creates a download url given the name
        :param name:
        :return:
        """
        return self.cc_base_url + name

    def __def_get_remote_index(self):
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
        self.logger.info('executing: %s', cmd)
        stdout_data = subprocess.getoutput(cmd)

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
        local_filepath = os.path.join(self.local_download_dir_warc, local_filename)

        if os.path.isfile(local_filepath) and self.reuse_previously_downloaded_files:
            self.logger.info("found local file, not downloading again (check reuse_previously_downloaded_files to "
                             "control this behaviour)")
            return local_filepath
        else:
            self.logger.info('downloading %s (local: %s)', url, local_filepath)
            urlretrieve(url, local_filepath, reporthook=self.__on_download_progress_update)
            self.logger.info('download completed, local file: %s', local_filepath)
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
                if record.rec_type == 'response':
                    counter_article_total += 1

                    # if the article passes filter tests, we notify the user
                    filter_pass, article = self.__filter_record(record)
                    if filter_pass:
                        counter_article_passed += 1

                        if not article:
                            article = NewsPlease.from_warc(record)

                        self.logger.info('article pass (%s; %s; %s)', article.sourceDomain, article.publish_date,
                                         article.title)
                        self.on_valid_article_extracted(article)
                    else:
                        counter_article_discarded += 1

                        if article:
                            self.logger.info('article discard (%s; %s; %s)', article.sourceDomain, article.publish_date,
                                             article.title)
                        else:
                            self.logger.info('article discard (%s)', record.rec_headers.get_header('WARC-Target-URI'))

                    if counter_article_total % 10 == 0:
                        elapsed_secs = time.time() - start_time
                        secs_per_article = elapsed_secs / counter_article_total
                        self.logger.info('statistics')
                        self.logger.info('pass = %i, discard = %i, total = %i', counter_article_passed,
                                         counter_article_discarded, counter_article_total)
                        self.logger.info('extraction from current WARC file started %s; %f s/article',
                                         human(start_time), secs_per_article)

    def run(self):
        """
        Main execution method, which consists of: get an up-to-date list of WARC files, and for each of them: download
        and extract articles. Each articles are checked against a filter. Finally, for each valid article the method
        on_valid_article_extracted will be invoked.
        :return:
        """
        self.__setup__()

        self.cc_news_crawl_names = self.__def_get_remote_index()
        self.logger.info('found %i files at commoncrawl.org', len(self.cc_news_crawl_names))

        # iterate the list of crawl_names, and for each: download and process it
        for name in self.cc_news_crawl_names:
            download_url = self.__get_download_url(name)
            local_path_name = self.__download(download_url)
            self.__process_warc_gz_file(local_path_name)

    def __get_pretty_filepath(self, path, article):
        """
        Pretty might be an euphemism, but this function tries to avoid too long filenames, while keeping some structure.
        :param path:
        :param name:
        :return:
        """
        short_filename = hashlib.sha256(article.filename.encode()).hexdigest()
        sub_dir = article.sourceDomain
        final_path = path + sub_dir + '/'
        if not os.path.exists(final_path):
            os.makedirs(final_path)
        return final_path + short_filename + '.json'

    def on_valid_article_extracted(self, article):
        """
        This function will be invoked for each article that was extracted successfully from the archived data and that
        satisfies the filter criteria.
        :param article:
        :return:
        """
        # do whatever you need to do with the article (e.g., save it to disk, store it in ElasticSearch, etc.)
        with open(self.__get_pretty_filepath(self.local_download_dir_article, article), 'w') as outfile:
            json.dump(article, outfile, indent=4, sort_keys=True)
        # ...

        return


if __name__ == '__main__':
    configure_logging({"LOG_LEVEL": "ERROR"})
    common_crawl = CommonCrawl()
    common_crawl.run()
