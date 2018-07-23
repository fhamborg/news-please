# -*- coding: utf-8 -*-
"""
This is the config-loading and json-loading module which loads and parses the
config file as well as the json file.

It handles the [General]-Section of the config.

All object-getters create deepcopies.
"""

import logging
from copy import deepcopy

import hjson

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

from ast import literal_eval
from scrapy.utils.log import configure_logging
import os


class CrawlerConfig(object):
    """
    The actual class. First parameter: config-file.
    This class is a singleton-class,
    Usage:
        First creation and loading of the config-file:
            c = CrawlerConfig.get_instance()
            c.setup(<config_file>)
        Further using:
            c = CrawlerConfig.get_instance()
    """

    # singleton-helper-class
    # Source: http://code.activestate.com/recipes/52558-the-singleton-pattern-implemented-with-python/#c4
    class SingletonHelper(object):
        """The singleton-helper-class"""

        # https://pythontips.com/2013/08/04/args-and-kwargs-in-python-explained/
        def __call__(self, *args, **kw):
            if CrawlerConfig.instance is None:
                CrawlerConfig.instance = CrawlerConfig()

            return CrawlerConfig.instance

    # singleton-helper-variable + function
    get_instance = SingletonHelper()
    instance = None

    # Here starts the actual class
    log = None
    log_output = []
    sections = None
    parser = None
    __current_section = None
    __scrapy_options = None
    __config = None

    def __init__(self):
        """
        The constructor

        (keep in mind: this is a singleton, so just called once)
        """

        if CrawlerConfig.instance is not None:
            self.log_output.append(
                {"level": "error",
                 "msg": "Multiple instances of singleton-class"})
            raise RuntimeError('Multiple instances of singleton-class')

    def setup(self, filepath):
        """
        Setup the actual class.

        :param str filepath: path to the config-file (including file-name)
        """
        if self.log is not None:
            self.log.warning("Disallowed multiple setup of config.")
            return

        self.log = logging.getLogger(__name__)
        self.parser = ConfigParser.RawConfigParser()
        self.parser.read(filepath)
        self.sections = self.parser.sections()
        self.log_output.append(
            {"level": "info", "msg": "Loading config-file (%s)" % filepath})
        self.load_config()
        self.handle_logging()

    def load_config(self):
        """
        Loads the config-file
        """
        self.__config = {}

        # Parse sections, its options and put it in self.config.
        for section in self.sections:

            self.__config[section] = {}
            options = self.parser.options(section)

            # Parse options of each section
            for option in options:

                try:
                    opt = self.parser \
                        .get(section, option)
                    try:
                        self.__config[section][option] = literal_eval(opt)
                    except (SyntaxError, ValueError):
                        self.__config[section][option] = opt
                        self.log_output.append(
                            {"level": "debug",
                             "msg": "Option not literal_eval-parsable"
                                    " (maybe string): [{0}] {1}"
                                 .format(section, option)})

                    if self.__config[section][option] == -1:
                        self.log_output.append(
                            {"level": "debug",
                             "msg": "Skipping: [%s] %s" % (section, option)}
                        )
                except ConfigParser.NoOptionError as exc:
                    self.log_output.append(
                        {"level": "error",
                         "msg": "Exception on [%s] %s: %s"
                                % (section, option, exc)}
                    )
                    self.__config[section][option] = None

    def get_scrapy_options(self):
        """
        :return: all options listed in the config section 'Scrapy'
        """
        if self.__scrapy_options is None:
            self.__scrapy_options = {}
            options = self.section("Scrapy")

            for key, value in options.items():
                self.__scrapy_options[key.upper()] = value
        return self.__scrapy_options

    def handle_logging(self):
        """
        To allow devs to log as early as possible, logging will already be
        handled here
        """

        configure_logging(self.get_scrapy_options())

        # Disable duplicates
        self.__scrapy_options["LOG_ENABLED"] = False

        # Now, after log-level is correctly set, lets log them.
        for msg in self.log_output:
            if msg["level"] is "error":
                self.log.error(msg["msg"])
            elif msg["level"] is "info":
                self.log.info(msg["msg"])
            elif msg["level"] is "debug":
                self.log.debug(msg["msg"])

    def config(self):
        """
        Get the whole config as a dict.

        :returns: The whole config as dict[section][option] (all lowercase)
        :rtype: dict
        """
        return deepcopy(self.__config)

    def section(self, section):
        """
        Get the whole section of a the config.

        :param section (string): The section to get all the options from.
        :return dict[option] (all lowercase)
        """
        return deepcopy(self.__config[section])

    def set_section(self, section):
        """
        Sets the current section to get the options from.

        :param section (string)
        """
        self.__current_section = section

    def option(self, option):
        """
        Gets the option, set_section needs to be set before.

        :param option (string): The option to get.
        :return mixed: The option from from the config.
        """
        if self.__current_section is None:
            raise RuntimeError('No section set in option-getting')
        return self.__config[self.__current_section][option]

    def get_working_path(self):
        """
        Gets the working path. If the path starts with a ~, this will be replaced by the current user's home path.
        :return:
        """
        self.set_section('Files')
        raw_path = self.option("working_path")
        if raw_path.startswith('~'):
            raw_path = os.path.expanduser('~') + raw_path[1:]

        return raw_path


class JsonConfig(object):
    """
    The actual class. First parameter: config-file.
    This class is a singleton-class,
    Usage:
        First creation and loading of the config-file:
            c = JsonConfig.get_instance()
            c.setup(<config_file>)
        Further using:
            c = JsonConfig.get_instance()
    """

    # singleton-helper-class
    # Source: http://code.activestate.com/recipes/52558-the-singleton-pattern-implemented-with-python/#c4
    class SingletonHelper(object):
        """The singleton-helper-class"""

        def __call__(self, *args, **kw):
            if JsonConfig.instance is None:
                JsonConfig.instance = JsonConfig()

            return JsonConfig.instance

    # singleton-helper-variable + function
    get_instance = SingletonHelper()
    instance = None

    # Here starts the actual class!
    log = None
    __json_object = None

    def __init__(self):
        """
        The constructor

        (keep in mind: this is a singleton, so just called once)
        """
        self.log = logging.getLogger(__name__)
        if JsonConfig.instance is not None:
            self.log.error('Multiple instances of singleton-class')
            raise RuntimeError('Multiple instances of singleton-class')

    def setup(self, filepath):
        """
        Setup the actual class.

        :param str filepath: path to the config-file (including file-name)
        """
        self.log.debug("Loading JSON-file (%s)", filepath)
        self.load_json(filepath)

    def load_json(self, filepath):
        """
        Loads the JSON-file from the filepath.

        :param filepath (string): The location of the JSON-file.
        """
        self.__json_object = hjson.load(open(filepath, 'r'))

    def config(self):
        """
        Get the whole JSON as a dict.

        :return dict
        """
        return deepcopy(self.__json_object)

    def get_site_objects(self):
        """
        Get the object containing all sites.

        :return sites (dict): The sites from the JSON-file
        """
        return deepcopy(self.__json_object["base_urls"])

    def get_url_array(self):
        """
        Get all url-objects in an array

        :return sites (array): The sites from the JSON-file
        """
        urlarray = []
        for urlobjects in self.__json_object["base_urls"]:
            urlarray.append(urlobjects["url"])
        return urlarray
