import locale
import re

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from lxml import html

from .abstract_extractor import AbstractExtractor


class LangExtractor(AbstractExtractor):
    """This class implements LangDetect as an article extractor but it can only
    detect the extracted language (en, de, ...).

    """

    def __init__(self):
        self.name = "langdetect"
        self.langcode_pattern = re.compile(r'\b[a-zA-Z]{2}(?=([-_]|\b))')

    def _language(self, item):
        """Returns the language of the extracted article by analyzing metatags and inspecting the visible text
        with langdetect"""

        response = item['spider_response'].body
        try:
            root = html.fromstring(response)
        except ValueError:
            root = html.fromstring(response.encode("utf-8"))

        # Check for lang-attributes
        lang = root.get('lang')

        if lang is None:
            lang = root.get('xml:lang')

        # Check for general meta tags
        if lang is None:
            meta = root.cssselect('meta[name="language"]')
            if len(meta) > 0:
                lang = meta[0].get('content')

        # Check for open graph tags
        if lang is None:
            meta = root.cssselect('meta[property="og:locale"]')
            if len(meta) > 0:
                lang = meta[0].get('content')

        # Look for <article> elements and inspect the one with the largest payload with langdetect
        if lang is None:
            article_list = []
            for article in root.xpath('//article'):
                article_list.append(re.sub(r'\s+', ' ', article.text_content().strip()))
                longest_articles = sorted(article_list, key=lambda article: len(article), reverse=True)
                for article in longest_articles:
                    try:
                        lang = detect(article)
                    except LangDetectException:
                        continue
                    else:
                        break

        # Analyze the whole body with langdetect
        if lang is None:
            try:
                lang = detect(root.text_content().strip())
            except LangDetectException:
                pass

        # Try to normalize output
        if lang is not None:
            # First search for suitable locale in the original output
            matches = self.langcode_pattern.search(lang)
            if matches is not None:
                lang = matches.group(0)
            else:
                # If no match was found, normalize the original output and search again
                normalized = locale.normalize(re.split(r'\s|;|,', lang.strip())[0])
                matches = self.langcode_pattern.search(normalized)
                if matches is not None:
                    lang = matches.group(0)

        return lang
