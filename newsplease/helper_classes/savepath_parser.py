"""
Helper class for parsing the savepath defined in the config.
"""
import hashlib
import ntpath
import os
import re
import time

from .url_extractor import UrlExtractor

# to improve performance, regex statements are compiled only once per module
re_time_exec = re.compile(r'%time_execution\(([^\)]+)\)')
re_timestamp_exec = re.compile(r'%timestamp_execution')

re_working_path = re.compile(r'%working_path')
re_time_dl = re.compile(r'%time_download\(([^\)]+)\)')
re_timstamp_dl = re.compile(r'%timestamp_download')
re_domain = re.compile(r'%domain\(([^\)]+)\)')
re_appendmd5_domain = re.compile(r'%appendmd5_domain\(([^\)]+)\)')
re_md5_domain = re.compile(r'%md5_domain\(([^\)]+)\)')
re_full_domain = re.compile(r'%full_domain\(([^\)]+)\)')
re_appendmd5_full_domain = re.compile(r'%appendmd5_full_domain\(([^\)]+)\)')
re_md5_full_domain = re.compile(r'%md5_full_domain\(([^\)]+)\)')
re_subdomains = re.compile(r'%subdomains\(([^\)]+)\)')
re_appendmd5_subdomains = re.compile(r'%appendmd5_subdomains\(([^\)]+)\)')
re_md5_subdomains = re.compile(r'%md5_subdomains\(([^\)]+)\)')
re_url_dir = re.compile(r'%url_directory_string\(([^\)]+)\)')
re_appendmd5_url_dir = re.compile(r'%appendmd5_url_directory_string\(([^\)]+)\)')
re_md5_url_dir = re.compile(r'%md5_url_directory_string\(([^\)]+)\)')
re_url_file = re.compile(r'%url_file_name\(([^\)]+)\)')
re_md5_url_file = re.compile(r'%md5_url_file_name\(([^\)]+)\)')
re_max_url_file = re.compile(r'%max_url_file_name')
re_appendmd5_max_url_file = re.compile(r'%appendmd5_max_url_file_name')


class SavepathParser(object):
    """
    This class contains methods to parse the given savepath
    """
    helper = None
    cfg_savepath = None
    relative_to_path = None
    format_relative_path = None
    working_path = None

    def __init__(
            self,
            cfg_savepath,
            relative_to_path,
            format_relative_path,
            helper,
            working_path
    ):
        self.helper = helper

        # this part can be replaced right now; no need to replace it over and
        # over every time get_savepath is called
        timestamp_execution = int(time.time())

        # lambda is used for lazy evalutation
        cfg_savepath = re.sub(r'%time_execution\(([^\)]+)\)',
                              lambda match: self.time_replacer
                              (match, timestamp_execution), cfg_savepath)
        cfg_savepath = re.sub(r'%timestamp_execution',
                              str(timestamp_execution), cfg_savepath)
        self.cfg_savepath = cfg_savepath

        self.relative_to_path = relative_to_path

        self.format_relative_path = format_relative_path

        self.working_path = working_path

    @staticmethod
    def time_replacer(match, timestamp):
        """
        Transforms the timestamp to the format the regex match determines.

        :param str match: the regex match
        :param time timestamp: the timestamp to format with match.group(1)
        :return str: the timestamp formated with strftime the way the
                     regex-match within the first set of braces defines
        """
        # match.group(0) = entire match
        # match.group(1) = match in braces #1
        return time.strftime(match.group(1), time.gmtime(timestamp))

    @staticmethod
    def append_md5_if_too_long(component, size):
        """
        Trims the component if it is longer than size and appends the
        component's md5. Total must be of length size.

        :param str component: component to work on
        :param int size: component's size limit
        :return str: component and appended md5 trimmed to be of length size
        """

        if len(component) > size:
            if size > 32:
                component_size = size - 32 - 1
                return "%s_%s" % (component[:component_size],
                                  hashlib.md5(component.encode('utf-8')).hexdigest())
            else:
                return hashlib.md5(component.encode('utf-8')).hexdigest()[:size]
        else:
            return component

    def get_savepath(self, url, savepath=None):
        """
        Evaluates the savepath with the help of the given url.

        :param str url: url to evaluate the savepath with
        :return str: the evaluated savepath for the given url
        """
        timestamp = int(time.time())

        if not savepath:
            savepath = self.cfg_savepath

        # lambda is used for lazy evaluation
        savepath = re.sub(re_working_path, lambda match: self.working_path, savepath)

        savepath = re.sub(
            re_time_dl, lambda match: SavepathParser.time_replacer(match, timestamp),
            savepath
        )
        savepath = re.sub(re_timstamp_dl, str(timestamp), savepath)

        savepath = re.sub(
            re_domain, lambda match: UrlExtractor.get_allowed_domain(url, False)
            [:int(match.group(1))], savepath
        )
        savepath = re.sub(
            re_appendmd5_domain, lambda match: SavepathParser.append_md5_if_too_long(
                UrlExtractor.get_allowed_domain(url, False), int(match.group(1))
            ), savepath
        )
        savepath = re.sub(
            re_md5_domain, lambda match: hashlib.md5(
                UrlExtractor.get_allowed_domain(url, False).encode('utf-8')
            ).hexdigest()[:int(match.group(1))], savepath
        )

        savepath = re.sub(
            re_full_domain, lambda match: UrlExtractor.get_allowed_domain(url)
            [:int(match.group(1))], savepath
        )
        savepath = re.sub(
            re_appendmd5_full_domain, lambda match: SavepathParser.append_md5_if_too_long(
                UrlExtractor.get_allowed_domain(url), int(match.group(1))
            ), savepath
        )
        savepath = re.sub(
            re_md5_full_domain, lambda match: hashlib.md5(
                UrlExtractor.get_allowed_domain(url).encode('utf-8')
            ).hexdigest()[:int(match.group(1))], savepath
        )

        savepath = re.sub(
            re_subdomains, lambda match: UrlExtractor.get_subdomain(url)
            [:int(match.group(1))], savepath
        )
        savepath = re.sub(
            re_appendmd5_subdomains, lambda match: SavepathParser.
            append_md5_if_too_long(UrlExtractor.get_subdomain(url), int(match.group(1))),
            savepath
        )
        savepath = re.sub(
            re_md5_subdomains, lambda match: hashlib.md5(
                UrlExtractor.get_subdomain(url).encode('utf-8')
            ).hexdigest()[:int(match.group(1))], savepath
        )

        savepath = re.sub(
            re_url_dir, lambda match: UrlExtractor.get_url_directory_string(url)
            [:int(match.group(1))], savepath
        )
        savepath = re.sub(
            re_appendmd5_url_dir, lambda match: SavepathParser.append_md5_if_too_long(
                UrlExtractor.get_url_directory_string(url), int(match.group(1))
            ), savepath
        )
        savepath = re.sub(
            re_md5_url_dir, lambda match: hashlib.md5(
                UrlExtractor.get_url_directory_string(url).encode('utf-8')
            ).hexdigest()[:int(match.group(1))], savepath
        )

        savepath = re.sub(
            re_url_file, lambda match: UrlExtractor.get_url_file_name(url)
            [:int(match.group(1))], savepath
        )
        savepath = re.sub(
            re_md5_url_file, lambda match: hashlib.md5(
                UrlExtractor.get_url_file_name(url).encode('utf-8')
            ).hexdigest()[:int(match.group(1))], savepath
        )

        abs_savepath = self.get_abs_path(savepath)

        savepath = re.sub(
            re_max_url_file, lambda match: UrlExtractor.get_url_file_name(url)
            [:SavepathParser.get_max_url_file_name_length(abs_savepath)], savepath
        )
        savepath = re.sub(
            re_appendmd5_max_url_file, lambda match: SavepathParser.
            append_md5_if_too_long(
                UrlExtractor.get_url_file_name(url),
                SavepathParser.get_max_url_file_name_length(abs_savepath)
            ), savepath
        )

        # ensure the savepath doesn't contain any invalid characters
        return SavepathParser.remove_not_allowed_chars(savepath)

    @staticmethod
    def remove_not_allowed_chars(savepath):
        """
        Removes invalid filepath characters from the savepath.

        :param str savepath: the savepath to work on
        :return str: the savepath without invalid filepath characters
        """
        split_savepath = os.path.splitdrive(savepath)
        # https://msdn.microsoft.com/en-us/library/aa365247.aspx
        savepath_without_invalid_chars = re.sub(r'<|>|:|\"|\||\?|\*', '_',
                                                split_savepath[1])
        return split_savepath[0] + savepath_without_invalid_chars

    @staticmethod
    def get_abs_path_static(savepath, relative_to_path):
        """
        Figures out the savepath's absolute version.

        :param str savepath: the savepath to return an absolute version of
        :param str relative_to_path: the file path this savepath should be
                                     relative to
        :return str: absolute version of savepath
        """
        if os.path.isabs(savepath):
            return os.path.abspath(savepath)
        else:
            return os.path.abspath(
                os.path.join(relative_to_path, (savepath))
            )

    def get_abs_path(self, savepath):
        """
        Determines the savepath's absolute version relative to the cfg file
        path.

        :param str savepath: the savepath to return an absolute version of
        :return str: absolute version of savepath
        """
        return self.get_abs_path_static(savepath, self.relative_to_path)

    @staticmethod
    def get_base_path(path):
        """
        Determines the longest possible beginning of a path that does not
        contain a %-Symbol.

        /this/is/a/pa%th would become /this/is/a

        :param str path: the path to get the base from
        :return: the path's base
        """
        if "%" not in path:
            return path

        path = os.path.split(path)[0]

        while "%" in path:
            path = os.path.split(path)[0]

        return path

    def get_formatted_relative_path(self, path):
        """
        Formates path to not start with a leading './' or '.\' if enables in
        the config

        :param str path: the path to format
        :return str: the [formatted] path
        """
        if self.format_relative_path and \
                (path.startswith('./') or path.startswith('.\\')):
            return path[2:]
        else:
            return path

    @staticmethod
    def get_max_url_file_name_length(savepath):
        """
        Determines the max length for any max... parts.

        :param str savepath: absolute savepath to work on
        :return: max. allowed number of chars for any of the max... parts
        """
        number_occurrences = savepath.count('%max_url_file_name')
        number_occurrences += savepath.count('%appendmd5_max_url_file_name')

        savepath_copy = savepath
        size_without_max_url_file_name = len(
            savepath_copy.replace('%max_url_file_name', '')
                .replace('%appendmd5_max_url_file_name', '')
        )

        # Windows: max file path length is 260 characters including
        # NULL (string end)
        max_size = 260 - 1 - size_without_max_url_file_name
        max_size_per_occurrence = max_size / number_occurrences

        return max_size_per_occurrence

    @staticmethod
    def get_filename(savepath):
        """
        Returns only the filename of the given path.
        :param savepath:
        :return:
        """
        return ntpath.basename(savepath)
