import logging
import os
import shutil
import signal
import sys
import threading
import time
from distutils.dir_util import copy_tree
from subprocess import Popen

import plac
import pymysql
from elasticsearch import Elasticsearch
from scrapy.utils.log import configure_logging

cur_path = os.path.dirname(os.path.realpath(__file__))
par_path = os.path.dirname(cur_path)
sys.path.append(cur_path)
sys.path.append(par_path)
from newsplease.helper_classes.savepath_parser import SavepathParser
from newsplease.config import JsonConfig
from newsplease.config import CrawlerConfig

try:
    import builtins
except ImportError:
    from future import builtins
if sys.version_info[0] < 3:
    ConnectionError = OSError


class NewsPleaseLauncher(object):
    """
    This class is supposed to be called initially to start all processes.  It
    sets up and manages all crawlers.
    """
    python_command = None
    crawlers = []
    cfg = None
    log = None
    cfg_directory_path = None
    cfg_file_path = None
    json_file_path = None
    shall_resume = False
    no_confirm = False
    threads = []
    threads_daemonized = []
    crawler_list = None
    daemon_list = None
    shutdown = False
    thread_event = None
    mysql = None
    elasticsearch = None
    number_of_active_crawlers = 0
    config_directory_default_path = "~/news-please-repo/config/"
    config_file_default_name = "config.cfg"
    library_mode = None

    __single_crawler = False

    def __init__(self, cfg_directory_path, is_resume, is_reset_elasticsearch, is_reset_json, is_reset_mysql,
                 is_no_confirm, library_mode=False):
        """
        The constructor of the main class, thus the real entry point to the tool.
        :param cfg_file_path:
        :param is_resume:
        :param is_reset_elasticsearch:
        :param is_reset_json:
        :param is_reset_mysql:
        :param is_no_confirm:
        """
        configure_logging({"LOG_LEVEL": "ERROR"})
        self.log = logging.getLogger(__name__)

        # other parameters
        self.shall_resume = is_resume
        self.no_confirm = is_no_confirm
        self.library_mode = library_mode

        # Sets an environmental variable called 'CColon', so scripts can import
        # modules of this project in relation to this script's dir
        # example: sitemap_crawler can import UrlExtractor via
        #   from newsplease.helper_classderes.url_extractor import UrlExtractor
        os.environ['CColon'] = os.path.abspath(os.path.dirname(__file__))

        # set stop handlers
        self.set_stop_handler()

        # threading
        self.thread_event = threading.Event()

        # Get & set CFG and JSON locally.
        if cfg_directory_path:
            # if a path was given by the user
            self.cfg_directory_path = self.get_expanded_path(cfg_directory_path)
        else:
            # if no path was given by the user, use default
            self.cfg_directory_path = self.get_expanded_path(self.config_directory_default_path)
        # init cfg path if empty
        self.init_config_file_path_if_empty()
        self.cfg_file_path = self.cfg_directory_path + self.config_file_default_name

        # config
        self.cfg = CrawlerConfig.get_instance()
        self.cfg.setup(self.cfg_file_path)
        self.mysql = self.cfg.section("MySQL")
        self.elasticsearch = self.cfg.section("Elasticsearch")

        # perform reset if given as parameter
        if is_reset_mysql:
            self.reset_mysql()
        if is_reset_json:
            self.reset_files()
        if is_reset_elasticsearch:
            self.reset_elasticsearch()
        # close the process
        if is_reset_elasticsearch or is_reset_json or is_reset_mysql:
            sys.exit(0)

        self.json_file_path = self.cfg_directory_path + self.cfg.section('Files')['url_input_file_name']

        self.json = JsonConfig.get_instance()
        self.json.setup(self.json_file_path)

        self.crawler_list = self.CrawlerList()
        self.daemon_list = self.DaemonList()

        self.__single_crawler = self.get_abs_file_path("./single_crawler.py", True, False)

        self.manage_crawlers()

    def set_stop_handler(self):
        """
        Initializes functions that are invoked when the user or OS wants to kill this process.
        :return:
        """
        signal.signal(signal.SIGTERM, self.graceful_stop)
        signal.signal(signal.SIGABRT, self.graceful_stop)
        signal.signal(signal.SIGINT, self.graceful_stop)

    @staticmethod
    def has_arg(string):
        """
        Determines if the string passed to this method was passed to the
        script.

        :param str string: string to test
        :rtype: bool
        """
        return len([arg for arg in sys.argv if arg == string]) != 0

    def manage_crawlers(self):
        """
        Manages all crawlers, threads and limites the number of parallel
        running threads.
        """
        sites = self.json.get_site_objects()
        for index, site in enumerate(sites):
            if "daemonize" in site:
                self.daemon_list.add_daemon(index, site["daemonize"])
            elif "additional_rss_daemon" in site:
                self.daemon_list.add_daemon(index,
                                            site["additional_rss_daemon"])
                self.crawler_list.append_item(index)
            else:
                self.crawler_list.append_item(index)

        num_threads = self.cfg.section('Crawler')[
            'number_of_parallel_crawlers']
        if self.crawler_list.len() < num_threads:
            num_threads = self.crawler_list.len()

        for _ in range(num_threads):
            thread = threading.Thread(target=self.manage_crawler,
                                      args=(),
                                      kwargs={})
            self.threads.append(thread)
            thread.start()

        num_daemons = self.cfg.section('Crawler')['number_of_parallel_daemons']
        if self.daemon_list.len() < num_daemons:
            num_daemons = self.daemon_list.len()

        for _ in range(num_daemons):
            thread_daemonized = threading.Thread(target=self.manage_daemon,
                                                 args=(),
                                                 kwargs={})
            self.threads_daemonized.append(thread_daemonized)
            thread_daemonized.start()

        while not self.shutdown:
            try:
                time.sleep(10)
                # if we are not in daemon mode and no crawler is running any longer,
                # all articles have been crawled and the tool can shut down
                if self.daemon_list.len() == 0 and self.number_of_active_crawlers == 0:
                    self.graceful_stop()
                    break

            except IOError:
                # This exception will only occur on kill-process on windows.
                # The process should be killed, thus this exception is
                # irrelevant.
                pass

    def manage_crawler(self):
        """
        Manages a normal crawler thread.

        When a crawler finished, it loads another one if there are still sites
        to crawl.
        """
        index = True
        self.number_of_active_crawlers += 1
        while not self.shutdown and index is not None:
            index = self.crawler_list.get_next_item()
            if index is None:
                self.number_of_active_crawlers -= 1
                break

            self.start_crawler(index)

    def manage_daemon(self):
        """
        Manages a daemonized crawler thread.

        Once a crawler it finished, it loads the next one.
        """
        while not self.shutdown:
            # next scheduled daemon, tuple (time, index)
            item = self.daemon_list.get_next_item()
            cur = time.time()
            pajama_time = item[0] - cur
            if pajama_time > 0:
                self.thread_event.wait(pajama_time)
            if not self.shutdown:
                self.start_crawler(item[1], daemonize=True)

    def start_crawler(self, index, daemonize=False):
        """
        Starts a crawler from the input-array.

        :param int index: The array-index of the site
        :param int daemonize: Bool if the crawler is supposed to be daemonized
                              (to delete the JOBDIR)
        """
        call_process = [sys.executable,
                        self.__single_crawler,
                        self.cfg_file_path,
                        self.json_file_path,
                        "%s" % index,
                        "%s" % self.shall_resume,
                        "%s" % daemonize]

        self.log.debug("Calling Process: %s", call_process)

        crawler = Popen(call_process,
                        stderr=None,
                        stdout=None)
        crawler.communicate()
        self.crawlers.append(crawler)

    def graceful_stop(self, signal_number=None, stack_frame=None):
        """
        This function will be called when a graceful-stop is initiated.
        """
        stop_msg = "Hard" if self.shutdown else "Graceful"
        if signal_number is None:
            self.log.info("%s stop called manually. "
                          "Shutting down.", stop_msg)
        else:
            self.log.info("%s stop called by signal #%s. Shutting down."
                          "Stack Frame: %s",
                          stop_msg, signal_number, stack_frame)
        self.shutdown = True
        self.crawler_list.stop()
        self.daemon_list.stop()
        self.thread_event.set()
        return True

    def init_config_file_path_if_empty(self):
        """
        if the config file path does not exist, this function will initialize the path with a default
        config file
        :return
        """

        if os.path.exists(self.cfg_directory_path):
            return

        user_choice = 'n'
        if self.no_confirm:
            user_choice = 'y'
        else:
            sys.stdout.write(
                "Config directory does not exist at '" + os.path.abspath(self.cfg_directory_path) + "'. "
                + "Should a default configuration be created at this path? [Y/n] ")
            if sys.version_info[0] < 3:
                user_choice = raw_input()
            else:
                user_choice = input()
            user_choice = user_choice.lower().replace("yes", "y").replace("no", "n")

        if not user_choice or user_choice == '':  # the default is yes
            user_choice = "y"
        if "y" not in user_choice and "n" not in user_choice:
            sys.stderr.write("Wrong input, aborting.")
            sys.exit(1)
        if "n" in user_choice:
            sys.stdout.write("Config file will not be created. Terminating.")
            sys.exit(1)

        # copy the default config file to the new path
        copy_tree(os.environ['CColon'] + os.path.sep + 'config', self.cfg_directory_path)
        return

    def get_expanded_path(self, path):
        """
        expands a path that starts with an ~ to an absolute path
        :param path:
        :return:
        """
        if path.startswith('~'):
            return os.path.expanduser('~') + path[1:]
        else:
            return path

    def get_abs_file_path(self, rel_file_path,
                          quit_on_error=None, check_relative_to_path=True):
        """
        Returns the absolute file path of the given [relative] file path
        to either this script or to the config file.

        May throw a RuntimeError if quit_on_error is True.

        :param str rel_file_path: relative file path
        :param bool quit_on_error: determines if the script may throw an
                                   exception
        :return str: absolute file path of the given relative file path
        :raises RuntimeError: if the file path does not exist and
                              quit_on_error is True
        """
        if self.cfg_file_path is not None and \
                check_relative_to_path and \
                not self.cfg.section('Files')['relative_to_start_processes_file']:
            script_dir = os.path.dirname(self.cfg_file_path)
        else:
            # absolute dir this script is in
            script_dir = os.path.dirname(__file__)

        abs_file_path = os.path.abspath(
            os.path.join(script_dir, rel_file_path))

        if not os.path.exists(abs_file_path):
            self.log.error(abs_file_path + " does not exist.")
            if quit_on_error is True:
                raise RuntimeError("Imported file not found. Quit.")

        return abs_file_path

    def reset_mysql(self):
        """
        Resets the MySQL database.
        """

        confirm = self.no_confirm

        print("""
Cleanup MySQL database:
    This will truncate all tables and reset the whole database.
""")

        if not confirm:
            confirm = 'yes' in builtins.input(
                """
    Do you really want to do this? Write 'yes' to confirm: {yes}"""
                    .format(yes='yes' if confirm else ''))

        if not confirm:
            print("Did not type yes. Thus aborting.")
            return

        print("Resetting database...")

        try:
            # initialize DB connection
            self.conn = pymysql.connect(host=self.mysql["host"],
                                        port=self.mysql["port"],
                                        db=self.mysql["db"],
                                        user=self.mysql["username"],
                                        passwd=self.mysql["password"])
            self.cursor = self.conn.cursor()

            self.cursor.execute("TRUNCATE TABLE CurrentVersions")
            self.cursor.execute("TRUNCATE TABLE ArchiveVersions")
            self.conn.close()
        except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError,
                pymysql.IntegrityError, TypeError) as error:
            self.log.error("Database reset error: %s", error)

    def reset_elasticsearch(self):
        """
        Resets the Elasticsearch Database.
        """

        print("""
Cleanup Elasticsearch database:
    This will truncate all tables and reset the whole Elasticsearch database.
              """)

        confirm = self.no_confirm

        if not confirm:
            confirm = 'yes' in builtins.input(
                """
Do you really want to do this? Write 'yes' to confirm: {yes}"""
                    .format(yes='yes' if confirm else ''))

        if not confirm:
            print("Did not type yes. Thus aborting.")
            return

        try:
            # initialize DB connection
            es = Elasticsearch([self.elasticsearch["host"]],
                               http_auth=(self.elasticsearch["username"], self.elasticsearch["secret"]),
                               port=self.elasticsearch["port"],
                               use_ssl=self.elasticsearch["use_ca_certificates"],
                               verify_certs=self.elasticsearch["use_ca_certificates"],
                               ca_certs=self.elasticsearch["ca_cert_path"],
                               client_cert=self.elasticsearch["client_cert_path"],
                               client_key=self.elasticsearch["client_key_path"])

            print("Resetting Elasticsearch database...")
            es.indices.delete(index=self.elasticsearch["index_current"], ignore=[400, 404])
            es.indices.delete(index=self.elasticsearch["index_archive"], ignore=[400, 404])
        except ConnectionError as error:
            self.log.error("Failed to connect to Elasticsearch. "
                           "Please check if the database is running and the config is correct: %s" % error)

    def reset_files(self):
        """
        Resets the local data directory.
        """
        confirm = self.no_confirm

        path = SavepathParser.get_base_path(
            SavepathParser.get_abs_path_static(
                self.cfg.section("Files")["local_data_directory"],
                os.path.dirname(self.cfg_file_path)
            )
        )

        print("""
Cleanup files:
    This will delete {path} and all its contents.
""".format(path=path))

        if not confirm:
            confirm = 'yes' in builtins.input(
                """
    Do you really want to do this? Write 'yes' to confirm: {yes}"""
                    .format(yes='yes' if confirm else ''))

        if not confirm:
            print("Did not type yes. Thus aborting.")
            return

        print("Removing: {}".format(path))

        try:
            shutil.rmtree(path)
        except OSError as error:
            if not os.path.exists(path):
                self.log.error("%s does not exist.", path)
            self.log.error(error)

    class CrawlerList(object):
        """
        Class that manages all crawlers that aren't supposed to be daemonized.
        Exists to be able to use threading.Lock().
        """
        lock = None
        crawler_list = []
        graceful_stop = False

        def __init__(self):
            self.lock = threading.Lock()

        def append_item(self, item):
            """
            Appends the given item to the crawler_list.

            :param: item to append to the crawler_list.
            """
            self.lock.acquire()
            try:
                self.crawler_list.append(item)
            finally:
                self.lock.release()

        def len(self):
            """
            Determines the number of crawler in the list.

            :return int: crawler_list's length
            """
            return len(self.crawler_list)

        def get_next_item(self):
            """
            Pops the first crawler in the list.

            :return: crawler_list's first item
            """
            if self.graceful_stop:
                return None
            self.lock.acquire()
            try:
                if len(self.crawler_list) > 0:
                    item = self.crawler_list.pop(0)
                else:
                    item = None
            finally:
                self.lock.release()

            return item

        def stop(self):
            self.graceful_stop = True

    class DaemonList(object):
        """
        Class that manages all crawlers that are supposed to be daemonized.
        Exists to be able to use threading.Lock().
        """
        lock = None

        daemons = {}
        queue = []
        queue_times = []
        graceful_stop = False

        def __init__(self):
            self.queue = []
            self.lock = threading.Lock()

        def sort_queue(self):
            """
            Sorts the queue, so the tuple with the lowest index (first value)
            is the first element in the array.
            """
            self.queue = sorted(self.queue, key=lambda t: t[0])
            self.queue_times = sorted(self.queue_times)

        def len(self):
            """
            Determines the number of daemonized crawlers in the list.

            :return int: crawler_list's length
            """
            return len(self.daemons)

        def add_daemon(self, index, _time):
            """
            Adds a daemon to the queue.

            :param index: The index, usually the index of the site-object
            :param _time: The repetition-time (every _time seconds the crawler)
                starts again.
            """
            self.lock.acquire()
            try:
                self.daemons[index] = _time
                self.add_execution(time.time(), index)
            finally:
                self.lock.release()

        def add_execution(self, _time, index):
            """
            Adds an execution to the queue.
            When for this particular _time an execution is already scheduled,
            the time will be checked for one second later until a free slot
            is found.

            :param _time: The (unix)-timestamp when the crawler should be
                executed.
            :param index: The index, usually the index of the site-object
            """
            _time = int(_time)
            while _time in self.queue_times:
                _time += 1

            self.queue_times.append(_time)
            self.queue.append((_time, index))

        def get_next_item(self):
            """
            Gets the next daemon-item and adds the daemon to the queue again.
            (With the new scheduled time)
            """
            if self.graceful_stop:
                return None

            self.lock.acquire()
            self.sort_queue()

            try:
                item = self.queue.pop(0)
                prev_time = self.queue_times.pop(0)

                self.add_execution(
                    # prev + daemonize if in time, now + daemonize if in delay
                    max(prev_time, time.time()) + self.daemons[item[1]], item[1]
                )
            finally:
                self.lock.release()

            return item

        def stop(self):
            self.graceful_stop = True


@plac.annotations(
    cfg_file_path=plac.Annotation('path to the config file', 'option', 'c'),
    resume=plac.Annotation('resume crawling from last process', 'flag'),
    reset_elasticsearch=plac.Annotation('reset Elasticsearch indexes', 'flag'),
    reset_json=plac.Annotation('reset JSON files', 'flag'),
    reset_mysql=plac.Annotation('reset MySQL database', 'flag'),
    reset_all=plac.Annotation('combines all reset options', 'flag'),
    no_confirm=plac.Annotation('skip confirm dialogs', 'flag')
)
def cli(cfg_file_path, resume, reset_elasticsearch, reset_mysql, reset_json, reset_all, no_confirm):
    "A generic news crawler and extractor."

    if reset_all:
        reset_elasticsearch = True
        reset_json = True
        reset_mysql = True

    if cfg_file_path and not cfg_file_path.endswith(os.path.sep):
        cfg_file_path += os.path.sep

    NewsPleaseLauncher(cfg_file_path, resume, reset_elasticsearch, reset_json, reset_mysql, no_confirm)



def main():
    plac.call(cli)


if __name__ == "__main__":
    main()
