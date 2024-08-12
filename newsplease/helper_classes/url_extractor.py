"""
Helper class for url extraction.
"""

import logging
import os
import re
import ssl
from typing import Optional
from scrapy.http import Response
from http.client import HTTPResponse
from urllib.error import URLError
from newsplease.config import CrawlerConfig

try:
    from urlparse import urljoin, urlparse
except ImportError:
    from urllib.parse import urljoin, urlparse

try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

# len(".markdown") = 9
MAX_FILE_EXTENSION_LENGTH = 9

# to improve performance, regex statements are compiled only once per module
re_www = re.compile(r"^(www.)")
re_domain = re.compile(r"[^/.]+\.[^/.]+$")
re_sitemap = re.compile(r"Sitemap:\s([^\r\n#]*)", re.MULTILINE)


class UrlExtractor(object):
    """
    This class contains url related methods.
    """

    @staticmethod
    def get_allowed_domain(url: str, allow_subdomains: bool = True) -> str:
        """
        Determines the url's domain.

        :param str url: the url to extract the allowed domain from
        :param bool allow_subdomains: determines wether to include subdomains
        :return str: subdomains.domain.topleveldomain or domain.topleveldomain
        """
        if allow_subdomains:
            return re.sub(re_www, "", re.search(r"[^/]+\.[^/]+", url).group(0))
        else:
            return re.search(re_domain, UrlExtractor.get_allowed_domain(url)).group(0)

    @staticmethod
    def get_subdomain(url: str) -> str:
        """
        Determines the domain's subdomains.

        :param str url: the url to extract any subdomains from
        :return str: subdomains of url
        """
        allowed_domain = UrlExtractor.get_allowed_domain(url)
        return allowed_domain[
            : len(allowed_domain) - len(UrlExtractor.get_allowed_domain(url, False))
        ]

    @staticmethod
    def follow_redirects(url: str, check_certificate: bool = True) -> str:
        """
        Get's the url actual address by following forwards

        :param str url: the url to work on
        :param bool check_certificate:
        :return str: actual address of url
        """
        return UrlExtractor.request_url(url=url, check_certificate=check_certificate).url

    @staticmethod
    def request_url(url: str, check_certificate: bool = True) -> HTTPResponse:
        """
        :param str url: the url to work on
        :param bool check_certificate:
        :return HTTPResponse:
        """
        request = UrlExtractor.url_to_request_with_agent(url)

        if check_certificate:
            opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
            return opener.open(request).url

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        response = urllib2.urlopen(request, context=context)

        return response

    @staticmethod
    def check_sitemap_urls(domain_url: str, check_certificate: bool = True) -> list[str]:
        """Check if a set of sitemaps exists for the requested domain

        :param str domain_url: The URL to work on
        :param bool check_certificate:
        :return list[str] working_sitemap_paths: All available sitemap for the domain_url
        """
        working_sitemap_paths = []
        config = CrawlerConfig.get_instance()
        sitemap_patterns = config.section("Crawler").get("sitemap_patterns", [])
        for sitemap_path in sitemap_patterns:
            # check common patterns
            url_sitemap = urljoin(domain_url, sitemap_path)
            try:
                response = UrlExtractor.request_url(url=url_sitemap, check_certificate=check_certificate)
                # Keep sitemaps that exist, including those resulting from redirections
                if response.getcode() in [200, 301, 308]:
                    logging.debug(f"Found an existing sitemap: {response.url}")
                    working_sitemap_paths.append(response.url)
            except URLError:
                continue

        return working_sitemap_paths

    @staticmethod
    def get_robots_response(url: str, allow_subdomains: bool, check_certificate: bool = True) -> Optional[HTTPResponse]:
        """
        Retrieve robots.txt response if it exists

        :param str url: the url to work on
        :param bool check_certificate:
        :param bool allow_subdomains: Determines if the robot.txt may be the
                                      subdomain's
        :return: the robot.txt's HTTP response or None if it's not retrieved
        """
        redirect_url = UrlExtractor.follow_redirects(
            url="http://" + UrlExtractor.get_allowed_domain(url, allow_subdomains=allow_subdomains),
            check_certificate=check_certificate
        )

        # Get robots.txt
        parsed = urlparse(redirect_url)
        if allow_subdomains:
            url_netloc = parsed.netloc
        else:
            url_netloc = UrlExtractor.get_allowed_domain(parsed.netloc, False)

        robots_url = "{url.scheme}://{url_netloc}/robots.txt".format(
            url=parsed, url_netloc=url_netloc
        )
        try:
            response = UrlExtractor.request_url(url=robots_url, check_certificate=check_certificate)
            if response.getcode() == 200:
                return response
        except URLError:
            if allow_subdomains:
                return UrlExtractor.get_robots_response(
                    url=url,
                    allow_subdomains=False,
                    check_certificate=check_certificate
                )
        return None

    @staticmethod
    def sitemap_check(url: str, check_certificate: bool = True) -> bool:
        """
        Sitemap-Crawlers are supported by every site that has a
        Sitemap set in the robots.txt, or any sitemap present in the domain

        :param str url: the url to work on
        :param bool check_certificate:
        :return bool: Determines if a sitemap exists
        """
        robots_response = UrlExtractor.get_robots_response(
            url=url, allow_subdomains=True, check_certificate=check_certificate
        )
        if robots_response and robots_response.getcode() == 200:
            # Check if "Sitemap" is set
            return "Sitemap:" in robots_response.read().decode("utf-8")
        # Check if there is an existing sitemap outside of robots.txt
        sitemap_urls = UrlExtractor.check_sitemap_urls(domain_url=url, check_certificate=check_certificate)
        any_sitemap_found = len(sitemap_urls) > 0
        if not any_sitemap_found:
            logging.warning("Fatal: neither robots.txt nor sitemap found.")
        return any_sitemap_found

    @staticmethod
    def get_sitemap_urls(domain_url: str, allow_subdomains: bool, check_certificate: bool) -> list[str]:
        """Retrieve SitemapCrawler input URLs from robots.txt or sitemaps

        :param str domain_url: The URL to work on
        :param bool allow_subdomains: Determines if the robot.txt may be the
            subdomain's
        :param bool check_certificate:
        :return list[str]: robots.txt URL or available sitemaps
        """
        robots_response = UrlExtractor.get_robots_response(
            url=domain_url, allow_subdomains=allow_subdomains, check_certificate=check_certificate
        )
        if robots_response and robots_response.getcode() == 200:
            robots_content = robots_response.read().decode("utf-8")
            sitemap_urls = re_sitemap.findall(robots_content)
            return sitemap_urls
        return UrlExtractor.check_sitemap_urls(domain_url=domain_url, check_certificate=check_certificate)

    @staticmethod
    def get_rss_url(response: Response) -> str:
        """
        Extracts the rss feed's url from the scrapy response.

        :param scrapy_response response: the site to extract the rss feed from
        :return str: rss feed url
        """
        # if this throws an IndexError, then the webpage with the given url
        # does not contain a link of type "application/rss+xml"
        return response.urljoin(
            response.xpath('//link[contains(@type, "application/rss+xml")]')
            .xpath("@href")
            .extract()[0]
        )

    @staticmethod
    def get_start_url(url: str) -> str:
        """
        Determines the start url to start a crawler from

        :param str url: the url to extract the start url from
        :return str: http://subdomains.domain.topleveldomain/ of url
        """
        return "http://" + UrlExtractor.get_allowed_domain(url) + "/"

    @staticmethod
    def get_url_directory_string(url: str) -> str:
        """
        Determines the url's directory string.

        :param str url: the url to extract the directory string from
        :return str: the directory string on the server
        """
        domain = UrlExtractor.get_allowed_domain(url)

        splitted_url = url.split("/")

        # the following commented list comprehension could replace
        # the following for, if not and break statement
        # index = [index for index in range(len(splitted_url))
        #          if not re.search(domain, splitted_url[index]) is None][0]
        for index in range(len(splitted_url)):
            if re.search(domain, splitted_url[index]) is not None:
                if splitted_url[-1] == "":
                    splitted_url = splitted_url[index + 1 : -2]
                else:
                    splitted_url = splitted_url[index + 1 : -1]
                break

        return "_".join(splitted_url)

    @staticmethod
    def get_url_file_name(url: str) -> str:
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
    def url_to_request_with_agent(url: str) -> urllib2.Request:
        options = CrawlerConfig.get_instance().get_scrapy_options()
        user_agent = options["USER_AGENT"]
        return urllib2.Request(url, headers={"user-agent": user_agent})
