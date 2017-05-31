import logging
import subprocess
import sys
from urllib.request import urlretrieve

from hurry.filesize import size
from scrapy.utils.log import configure_logging
from warcio.archiveiterator import ArchiveIterator

from newsplease import NewsPlease


class CommonCrawl:
    # YOUR CONFIG ############
    # download dir, change this
    local_download_dir = './'
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

    def __filter_record(self, warc_record):
        """
        Returns true if a record passes all tests: hosts, publishing date
        :param warc_record:
        :return:
        """
        # filter by host
        if self.filter_valid_hosts:
            url = warc_record.rec_headers.get_header('WARC-Target-URI')

            # quite simple check
            for valid_host in self.filter_valid_hosts:
                if valid_host not in url:
                    return False

        # filter by date
        if self.filter_start_date or self.filter_end_date:
            publishing_date = self.__get_publishing_date(warc_record)
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

    def __get_publishing_date(self, warc_record):
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
            "aws s3 ls --recursive s3://commoncrawl/crawl-data/CC-NEWS/ --no-sign-request > tmpaws.txt && awk '{ print $4 }' tmpaws.txt && rm tmpaws.txt")
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
            percent = readsofar * 1e2 / totalsize
            s = "\r%s / %s" % (size(readsofar), size(totalsize))
            sys.stdout.write(s)
            if readsofar >= totalsize:  # near the end
                sys.stderr.write("\r")
        else:  # total size is unknown
            sys.stdout.write("\rread %s" % (size(readsofar)))

    def __download(self, url):
        """

        :param url: Where to download from
        :return: File path name of the downloaded file
        """
        self.logger.info('downloading %s', url)
        local_filename, headers = urlretrieve(url, reporthook=self.__on_download_progress_update)
        self.logger.info('download completed, local file: %s ()', local_filename)
        return local_filename

    def __process_warc_gz_file(self, path_name):
        with open(path_name, 'rb') as stream:
            for record in ArchiveIterator(stream):
                if record.rec_type == 'response':
                    if self.__filter_record(record):
                        article = NewsPlease.from_warc(record)

    def run(self):
        self.cc_news_crawl_names = self.__def_get_remote_index()
        self.logger.info('found %i files at commoncrawl.org', len(self.cc_news_crawl_names))

        # for name in self.cc_news_crawl_names:
        #    download_url = self.__get_download_url(name)
        #    local_path_name = self.__download(download_url)
        #    self.__process_warc_gz_file(local_path_name)
        tmpfile = '/var/folders/qg/vmj6zq4s7hb2pbkp3b8kstvh0000gn/T/tmp888c4xp3'
        self.__process_warc_gz_file(tmpfile)


if __name__ == '__main__':
    configure_logging({"LOG_LEVEL": "ERROR"})
    common_crawl = CommonCrawl()
    common_crawl.run()
