import copy
import threading

import requests


class SimpleCrawler(object):
    _results = {}

    @staticmethod
    def fetch_url(url, timeout=None):
        """
        Crawls the html content of the parameter url and returns the html
        :param url:
        :param timeout: in seconds, if None, the urllib default is used
        :return:
        """
        return SimpleCrawler._fetch_url(url, False, timeout=timeout)

    @staticmethod
    def _fetch_url(url, is_threaded, timeout=None):
        """
        Crawls the html content of the parameter url and saves the html in _results
        :param url:
        :param is_threaded: If True, results will be stored for later processing by the fetch_urls method. Else not.
        :param timeout: in seconds, if None, the urllib default is used
        :return: html of the url
        """
        headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2)'}
        req = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=20)
        req.mount('https://', adapter)
        req.mount('http://', adapter)
        getter = requests.get(url, timeout=timeout, headers=headers)
        if getter.ok:
            html = getter.content
        else:
            html = None
        if is_threaded:
            SimpleCrawler._results[url] = html

        return html

    @staticmethod
    def fetch_urls(urls, timeout=None):
        """
        Crawls the html content of all given urls in parallel. Returns when all requests are processed.
        :param urls:
        :param timeout: in seconds, if None, the urllib default is used
        :return:
        """
        threads = [threading.Thread(target=SimpleCrawler._fetch_url, args=(url, True, timeout)) for url in urls]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        results = copy.deepcopy(SimpleCrawler._results)
        SimpleCrawler._results = {}
        return results
