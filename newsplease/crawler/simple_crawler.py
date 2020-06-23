# Based on https://github.com/adbar/trafilatura/blob/master/trafilatura/utils.py
import logging
import socket
import copy
import threading

try:
    # this module is faster
    import cchardet
except ImportError:
    cchardet = None
# https://charset-normalizer.readthedocs.io/en/latest/
# https://ftfy.readthedocs.io/en/latest/

import requests
import urllib3

MAX_FILE_SIZE = 20000000
MIN_FILE_SIZE = 10

LOGGER = logging.getLogger(__name__)

# customize headers
HEADERS = {
    'Connection': 'close',  # another way to cover tracks
    'User-Agent': 'Mozilla/5.0'
}
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def isutf8(data):
    """Simple heuristic to determine if a bytestring uses standard unicode encoding"""
    try:
        data.decode('UTF-8')
    except UnicodeDecodeError:
        return False
    else:
        return True


def detect_encoding(bytesobject):
    """Read the first chunk of input and return its encoding"""
    # unicode-test
    if isutf8(bytesobject):
        return 'UTF-8'
    # try one of the installed detectors
    if cchardet is not None:
        guess = cchardet.detect(bytesobject)
        LOGGER.debug('guessed encoding: %s', guess['encoding'])
        return guess['encoding']
    # fallback on full response
    # if guess is None or guess['encoding'] is None: # or guess['confidence'] < 0.99:
    #    guessed_encoding = chardet.detect(bytesobject)['encoding']
    # return
    return None


def decode_response(response):
    """Read the first chunk of server response and decode it"""
    guessed_encoding = detect_encoding(response.content)
    LOGGER.debug('response/guessed encoding: %s / %s', response.encoding, guessed_encoding)
    # process
    if guessed_encoding is not None:
        try:
            htmltext = response.content.decode(guessed_encoding)
        except UnicodeDecodeError:
            LOGGER.warning('encoding error: %s / %s', response.encoding, guessed_encoding)
            htmltext = response.text
    else:
        htmltext = response.text
    return htmltext


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
        html_str = None
        # send
        try:
            # read by streaming chunks (stream=True, iter_content=xx)
            # so we can stop downloading as soon as MAX_FILE_SIZE is reached
            response = requests.get(url, timeout=timeout, verify=False, allow_redirects=True, headers=HEADERS)
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
            LOGGER.error('malformed URL: %s', url)
        except requests.exceptions.TooManyRedirects:
            LOGGER.error('redirects: %s', url)
        except requests.exceptions.SSLError as err:
            LOGGER.error('SSL: %s %s', url, err)
        except (
            socket.timeout, requests.exceptions.ConnectionError,
            requests.exceptions.Timeout, socket.error, socket.gaierror
        ) as err:
            LOGGER.error('connection: %s %s', url, err)
        else:
            # safety checks
            if response.status_code != 200:
                LOGGER.error('not a 200 response: %s', response.status_code)
            elif response.text is None or len(response.text) < MIN_FILE_SIZE:
                LOGGER.error('too small/incorrect: %s %s', url, len(response.text))
            elif len(response.text) > MAX_FILE_SIZE:
                LOGGER.error('too large: %s %s', url, len(response.text))
            else:
                html_str = decode_response(response)
        if is_threaded:
            SimpleCrawler._results[url] = html_str
        return html_str

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
