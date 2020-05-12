"""
This script should only be executed by the news-please initial script itself.

This script starts a crawler.
"""

import hashlib
import logging
import shutil
import sys
from ast import literal_eval

import os
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scrapy.spiderloader import SpiderLoader
from scrapy.utils.log import configure_logging

cur_path = os.path.dirname(os.path.realpath(__file__))
par_path = os.path.dirname(cur_path)
sys.path.append(cur_path)
sys.path.append(par_path)
from newsplease.config import CrawlerConfig
from newsplease.config import JsonConfig
from newsplease.helper import Helper
from newsplease.helper_classes.class_loader import ClassLoader
from newsplease.crawler.items import NewscrawlerItem

try:
    from _thread import start_new_thread
except ImportError:
    from thread import start_new_thread
from twisted.internet.error import ReactorAlreadyRunning


class SingleCrawler(object):
    """
    This class is called when this script is executed.

    It starts a single crawler, that is passed along to this script.
    """
    cfg = None
    json = None
    log = None
    crawler_name = None
    process = None
    helper = None
    cfg_file_path = None
    json_file_path = None
    cfg_crawler = None
    __scrapy_options = None
    __crawer_module = "newsplease.crawler.spiders"
    site_number = None
    shall_resume = False
    daemonize = False

    @classmethod
    def create_as_library(cls, url):
        """
        Creates a single crawler as in library mode. Crawling will start immediately.
        :param url:
        :return:
        """
        site = {
            "crawler": "Download",
            "url": url
        }
        cfg_file_path = os.path.dirname(__file__) + os.path.sep + 'config' + os.path.sep + 'config_lib.cfg'
        return cls(cfg_file_path, site, 0, False, False, True)

    def __init__(self, cfg_file_path, json_file_path,
                 site_index, shall_resume, daemonize, library_mode=False):
        # set up logging before it's defined via the config file,
        # this will be overwritten and all other levels will be put out
        # as well, if it will be changed.
        configure_logging({"LOG_LEVEL": "CRITICAL"})
        self.log = logging.getLogger(__name__)

        self.cfg_file_path = cfg_file_path
        self.json_file_path = json_file_path
        self.site_number = int(site_index)
        self.shall_resume = shall_resume \
            if isinstance(shall_resume, bool) else literal_eval(shall_resume)
        self.daemonize = daemonize \
            if isinstance(daemonize, bool) else literal_eval(daemonize)

        # set up the config file
        self.cfg = CrawlerConfig.get_instance()
        self.cfg.setup(self.cfg_file_path)
        self.log.debug("Config initialized - Further initialisation.")

        self.cfg_crawler = self.cfg.section("Crawler")

        # load the URL-input-json-file or - if in library mode - take the json_file_path as the site information (
        # kind of hacky..)
        if not library_mode:
            self.json = JsonConfig.get_instance()
            self.json.setup(self.json_file_path)
            sites = self.json.get_site_objects()
            site = sites[self.site_number]
        else:
            sites = [json_file_path]
            site = json_file_path

        if "ignore_regex" in site:
            ignore_regex = "(%s)|" % site["ignore_regex"]
        else:
            ignore_regex = "(%s)|" % \
                           self.cfg.section('Crawler')['ignore_regex']

        # Get the default crawler. The crawler can be overwritten by fallbacks.
        if "additional_rss_daemon" in site and self.daemonize:
            self.crawler_name = "RssCrawler"
        elif "crawler" in site:
            self.crawler_name = site["crawler"]
        else:
            self.crawler_name = self.cfg.section("Crawler")["default"]
        # Get the real crawler-class (already "fallen back")
        crawler_class = self.get_crawler(self.crawler_name, site["url"])

        if not self.cfg.section('Files')['relative_to_start_processes_file']:
            relative_to_path = os.path.dirname(self.cfg_file_path)
        else:
            # absolute dir this script is in
            relative_to_path = os.path.dirname(__file__)

        news_item_class_name = self.cfg.section("Scrapy").get("item_class", None)
        if not news_item_class_name:
            news_item_class = NewscrawlerItem
        else:
            news_item_class = ClassLoader.from_string(news_item_class_name)
            if not issubclass(news_item_class, NewscrawlerItem):
                raise ImportError("ITEM_CLASS must be a subclass of NewscrawlerItem")

        self.helper = Helper(self.cfg.section('Heuristics'),
                             self.cfg.section("Files")["local_data_directory"],
                             relative_to_path,
                             self.cfg.section('Files')['format_relative_path'],
                             sites,
                             crawler_class,
                             news_item_class,
                             self.cfg.get_working_path())

        self.__scrapy_options = self.cfg.get_scrapy_options()

        self.update_jobdir(site)

        # make sure the crawler does not resume crawling
        # if not stated otherwise in the arguments passed to this script
        self.remove_jobdir_if_not_resume()

        self.load_crawler(crawler_class,
                          site["url"],
                          ignore_regex)

        # start the job. if in library_mode, do not stop the reactor and so on after this job has finished
        # so that further jobs can be executed. it also needs to run in a thread since the reactor.run method seems
        # to not return. also, scrapy will attempt to start a new reactor, which fails with an exception, but
        # the code continues to run. we catch this excepion in the function 'start_process'.
        if library_mode:
            start_new_thread(start_process, (self.process, False,))
        else:
            self.process.start()

    def update_jobdir(self, site):
        """
        Update the JOBDIR in __scrapy_options for the crawler,
        so each crawler gets its own jobdir.

        :param object site: a site dict extracted from the json file
        """
        working_path = self.cfg.get_working_path()
        if not working_path.endswith("/"):
            working_path += "/"
        jobdirname = self.__scrapy_options["JOBDIRNAME"]
        if not jobdirname.endswith("/"):
            jobdirname += "/"

        site_string = ''.join(site["url"]) + self.crawler_name
        hashed = hashlib.md5(site_string.encode('utf-8'))

        self.__scrapy_options["JOBDIR"] = working_path + jobdirname + hashed.hexdigest()

    def get_crawler(self, crawler, url):
        """
        Checks if a crawler supports a website (the website offers e.g. RSS
        or sitemap) and falls back to the fallbacks defined in the config if
        the site is not supported.

        :param str crawler: Crawler-string (from the crawler-module)
        :param str url: the url this crawler is supposed to be loaded with
        :rtype: crawler-class or None
        """
        checked_crawlers = []
        while crawler is not None and crawler not in checked_crawlers:
            checked_crawlers.append(crawler)
            current = self.get_crawler_class(crawler)
            if hasattr(current, "supports_site"):
                supports_site = getattr(current, "supports_site")
                if callable(supports_site):
                    try:
                        crawler_supports_site = supports_site(url)
                    except Exception as e:
                        self.log.info(f'Crawler not supported due to: {str(e)}',
                                      exc_info=True)
                        crawler_supports_site = False

                    if crawler_supports_site:
                        self.log.debug("Using crawler %s for %s.",
                                       crawler, url)
                        return current
                    elif (crawler in self.cfg_crawler["fallbacks"] and
                                  self.cfg_crawler["fallbacks"][crawler] is not None):
                        self.log.warn("Crawler %s not supported by %s. "
                                      "Trying to fall back.", crawler, url)
                        crawler = self.cfg_crawler["fallbacks"][crawler]
                    else:
                        self.log.error("No crawlers (incl. fallbacks) "
                                       "found for url %s.", url)
                        raise RuntimeError("No crawler found. Quit.")
            else:
                self.log.warning("The crawler %s has no "
                                 "supports_site-method defined", crawler)
                return current
        self.log.error("Could not fall back since you created a fall back "
                       "loop for %s in the config file.", crawler)
        sys.exit(1)

    def get_crawler_class(self, crawler):
        """
        Searches through the modules in self.__crawer_module for a crawler with
        the name passed along.

        :param str crawler: Name of the crawler to load
        :rtype: crawler-class
        """
        settings = Settings()
        settings.set('SPIDER_MODULES', [self.__crawer_module])
        spider_loader = SpiderLoader(settings)
        return spider_loader.load(crawler)

    def load_crawler(self, crawler, url, ignore_regex):
        """
        Loads the given crawler with the given url.

        :param class crawler: class of the crawler to load
        :param str url: url to start the crawler with
        :param regex ignore_regex: to be able to ignore urls that match this
                                   regex code
        """
        self.process = CrawlerProcess(self.cfg.get_scrapy_options())
        self.process.crawl(
            crawler,
            self.helper,
            url=url,
            config=self.cfg,
            ignore_regex=ignore_regex)

    def remove_jobdir_if_not_resume(self):
        """
        This method ensures that there's no JOBDIR (with the name and path
        stated in the config file) any crawler would automatically resume
        crawling with if '--resume' isn't passed to this script.
        """
        jobdir = self.__scrapy_options["JOBDIR"]

        if (not self.shall_resume or self.daemonize) \
                and os.path.exists(jobdir):
            shutil.rmtree(jobdir)

            self.log.info("Removed " + jobdir + " since '--resume' was not passed to"
                                                " initial.py or this crawler was daemonized.")


def start_process(process, stop_after_job):
    try:
        process.start(stop_after_job)
    except ReactorAlreadyRunning:
        pass


if __name__ == "__main__":
    SingleCrawler(cfg_file_path=sys.argv[1],
                  json_file_path=sys.argv[2],
                  site_index=sys.argv[3],
                  shall_resume=sys.argv[4],
                  daemonize=sys.argv[5])
