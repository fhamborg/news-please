import json
import logging
import subprocess
import sys
import urllib
from urllib.request import urlretrieve

import os
from hurry.filesize import size
from scrapy.utils.log import configure_logging
from warcio.archiveiterator import ArchiveIterator

from newsplease import NewsPlease


class CommonCrawl:
    # YOUR CONFIG ############
    # download dir for warc files
    local_download_dir_warc = './cc_download_warc/'
    # download dir for articles
    local_download_dir_article = './cc_download_article/'
    # hosts (if None or empty list, any host is OK)
    filter_valid_hosts = []
    # start date (if None, any date is OK as start date), as datetime
    filter_start_date = None
    # end date (if None, any date is OK as end date)
    filter_end_date = None
    # if date filtering is string, e.g., if we could not detect the date of an article, we will discard the article
    filter_strict_date = True
    # END YOUR CONFIG #########

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

    def __filter_record(self, warc_record, article):
        """
        Returns true if a record passes all tests: hosts, publishing date
        :param warc_record:
        :return:
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
                    return False

        # filter by date
        if self.filter_start_date or self.filter_end_date:
            publishing_date = self.__get_publishing_date(warc_record, article)
            if not publishing_date:
                if self.filter_strict_date:
                    return False
            else:  # here we for sure have a date
                # is article published too early?
                if self.filter_start_date:
                    if publishing_date < self.filter_start_date:
                        return False
                if self.filter_end_date:
                    if publishing_date > self.filter_end_date:
                        return False

        return True

    def __get_publishing_date(self, warc_record, article):
        """
        Extracts the publishing date from the record
        :param warc_record:
        :return:
        """

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
        stdout_data = subprocess.getoutput(
            "aws s3 ls --recursive s3://commoncrawl/crawl-data/CC-NEWS/ --no-sign-request > tmpaws.txt && " +
            "awk '{ print $4 }' tmpaws.txt && " +
            "rm tmpaws.txt")
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

        self.logger.info('downloading %s (local: %s)', url, local_filepath)
        urlretrieve(url, local_filepath, reporthook=self.__on_download_progress_update)
        self.logger.info('download completed, local file: %s ()', local_filepath)

        return local_filepath

    def __process_warc_gz_file(self, path_name):
        """
        Iterates all transactions in one WARC file and for each transaction tries to extract an article object.
        Afterwards, each article is checked against the filter criteria and if all are passed, the function
        on_valid_article_extracted is invoked with the article object.
        :param path_name:
        :return:
        """
        with open(path_name, 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type == 'response':
                    article = NewsPlease.from_warc(record)

                    # if the article passes filter tests, we notify the user
                    if self.__filter_record(record, article):
                        self.on_valid_article_extracted(article)

    def run(self):
        """
        Main execution method, which consists of: get an up-to-date list of WARC files, and for each of them: download
        and extract articles. Each articles are checked against a filter. Finally, for each valid article the method
        on_valid_article_extracted will be invoked.
        :return:
        """
        self.cc_news_crawl_names = self.__def_get_remote_index()
        self.logger.info('found %i files at commoncrawl.org', len(self.cc_news_crawl_names))

        # iterate the list of crawl_names, and for each: download and process it
        for name in self.cc_news_crawl_names:
            download_url = self.__get_download_url(name)
            local_path_name = self.__download(download_url)
            self.__process_warc_gz_file(local_path_name)

            # for testing, it might be useful to execute the above (the normal workflow) and cancel the process when the
            # first file is downloaded. once that's happened, copy the filepath from the log, paste it down here and
            # uncomment the following two lines, but comment the for loop above. this way, the tool will not download all
            # the files and you can work with one file locally before doing the full process on large scale
            # tmpfile = '/var/folders/qg/vmj6zq4s7hb2pbkp3b8kstvh0000gn/T/tmp888c4xp3'
            # self.__process_warc_gz_file(tmpfile)

    def on_valid_article_extracted(self, article):
        """
        This function will be invoked for each article that was extracted successfully from the archived data and that
        satisfies the filter criteria.
        :param article:
        :return:
        """
        # do whatever you need to do with the article (probably save it to disk, e.g.
        with open(self.local_download_dir_article + article['filename'] + '.json', 'w') as outfile:
            json.dump(article, outfile, indent=4, sort_keys=True)
        # ...

        return


if __name__ == '__main__':
    configure_logging({"LOG_LEVEL": "ERROR"})
    common_crawl = CommonCrawl()
    common_crawl.run()
