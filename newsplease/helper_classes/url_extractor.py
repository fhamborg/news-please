"""
Helper class for url extraction.
"""
import os
import re
from newsplease.config import CrawlerConfig

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

# len(".markdown") = 9
MAX_FILE_EXTENSION_LENGTH = 9

# to improve performance, regex statements are compiled only once per module
re_www = re.compile(r'^(www.)')
re_domain = re.compile(r'[^/.]+\.[^/.]+$', )


class UrlExtractor(object):
    """
    This class contains url related methods.
    """

    @staticmethod
    def get_allowed_domain(url, allow_subdomains=True):
        """
        Determines the url's domain.

        :param str url: the url to extract the allowed domain from
        :param bool allow_subdomains: determines wether to include subdomains
        :return str: subdomains.domain.topleveldomain or domain.topleveldomain
        """
        if allow_subdomains:
            return re.sub(re_www, '', re.search(r'[^/]+\.[^/]+', url).group(0))
        else:
            return re.search(re_domain, UrlExtractor.get_allowed_domain(url)).group(0)

    @staticmethod
    def get_subdomain(url):
        """
        Determines the domain's subdomains.

        :param str url: the url to extract any subdomains from
        :return str: subdomains of url
        """
        allowed_domain = UrlExtractor.get_allowed_domain(url)
        return allowed_domain[:len(allowed_domain) - len(
            UrlExtractor.get_allowed_domain(url, False))]

    @staticmethod
    def follow_redirects(url):
        """
        Get's the url actual address by following forwards

        :param str url: the url to work on
        :return str: actual address of url
        """
        url = UrlExtractor.url_to_request_with_agent(url)
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
        return opener.open(url).url

    @staticmethod
    def get_sitemap_url(url, allow_subdomains):
        """
        Determines the domain's robot.txt

        :param str url: the url to work on
        :param bool allow_subdomains: Determines if the robot.txt may be the
                                      subdomain's
        :return: the robot.txt's address
        :raises Exception: if there's no robot.txt on the site's domain
        """
        if allow_subdomains:
            redirect = UrlExtractor.follow_redirects(
                "http://" + UrlExtractor.get_allowed_domain(url)
            )
        else:
            redirect = UrlExtractor.follow_redirects(
                "http://" +
                UrlExtractor.get_allowed_domain(url, False)
            )
        redirect = UrlExtractor.follow_redirects(url)

        # Get robots.txt
        parsed = urlparse(redirect)
        if allow_subdomains:
            url_netloc = parsed.netloc
        else:
            url_netloc = UrlExtractor.get_allowed_domain(
                parsed.netloc, False)

        robots = '{url.scheme}://{url_netloc}/robots.txt'.format(
            url=parsed, url_netloc=url_netloc)
        robots_req = UrlExtractor.url_to_request_with_agent(robots)
        try:
            urllib2.urlopen(robots_req)
            return robots
        except:
            if allow_subdomains:
                return UrlExtractor.get_sitemap_url(url, False)
            else:
                raise Exception('Fatal: no robots.txt found.')

    @staticmethod
    def sitemap_check(url):
        """
        Sitemap-Crawler are supported by every site which have a
        Sitemap set in the robots.txt.

        :param str url: the url to work on
        :return bool: Determines if Sitemap is set in the site's robots.txt
        """
        url = UrlExtractor.get_sitemap_url(url, True)
        url = UrlExtractor.url_to_request_with_agent(url)
        response = urllib2.urlopen(url)

        # Check if "Sitemap" is set
        return "Sitemap:" in response.read().decode('utf-8')

    def get_rss_url(self, response):
        """
        Extracts the rss feed's url from the scrapy response.

        :param scrapy_response response: the site to extract the rss feed from
        :return str: rss feed url
        """
        # if this throws an IndexError, then the webpage with the given url
        # does not contain a link of type "application/rss+xml"
        return response.urljoin(
            response.xpath(
                '//link[contains(@type, "application/rss+xml")]'
            ).xpath('@href').extract()[0]
        )

    @staticmethod
    def get_start_url(url):
        """
        Determines the start url to start a crawler from

        :param str url: the url to extract the start url from
        :return str: http://subdomains.domain.topleveldomain/ of url
        """
        return "http://" + UrlExtractor.get_allowed_domain(url) + "/"

    @staticmethod
    def get_url_directory_string(url):
        """
        Determines the url's directory string.

        :param str url: the url to extract the directory string from
        :return str: the directory string on the server
        """
        domain = UrlExtractor.get_allowed_domain(url)

        splitted_url = url.split('/')

        # the following commented list comprehension could replace
        # the following for, if not and break statement
        # index = [index for index in range(len(splitted_url))
        #          if not re.search(domain, splitted_url[index]) is None][0]
        for index in range(len(splitted_url)):
            if not re.search(domain, splitted_url[index]) is None:
                if splitted_url[-1] is "":
                    splitted_url = splitted_url[index + 1:-2]
                else:
                    splitted_url = splitted_url[index + 1:-1]
                break

        return '_'.join(splitted_url)

    @staticmethod
    def get_url_file_name(url):
        """
        Determines the url's file name.

        :param str url: the url to extract the file name from
        :return str: the filename (without the file extension) on the server
        """
        url_root_ext = os.path.splitext(url)

        if len(url_root_ext[1]) <= MAX_FILE_EXTENSION_LENGTH:
            return os.path.split(url_root_ext[0])[1]
        else:
            return os.path.split(url)[1]

    @staticmethod
    def url_to_request_with_agent(url):
        options = CrawlerConfig.get_instance().get_scrapy_options()
        user_agent = options['USER_AGENT']
        return urllib2.Request(url, headers={'user-agent': user_agent})
