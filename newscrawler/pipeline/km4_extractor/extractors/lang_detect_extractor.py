from newscrawler.pipeline.km4_extractor.extractors.abstract_extractor import *
from langdetect import detect
from lxml import html
import locale
import re

class Extractor(AbstractExtractor):
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
        root = html.fromstring(response)

        # Check for lang-attributes
        lang = root.get('lang')

        if lang is None:
            lang = root.get('xml:lang')

        # Check for general meta tags
        if lang is None:
            lang = root.cssselect('meta[name="language"]')[0].get('content')

        # Check for open graph tags
        if lang is None:
            lang = root.cssselect('meta[property="og:locale"]')[0].get('content')

        # Look for <article> elements and inspect the one with the largest payload with langdetect
        if lang is None:
            article_list = []
            for article in root.xpath('//article'):
                article_list.append(re.sub(r'\s+', ' ', article.text_content().strip()))
                if len(article_list) > 0:
                    lang = detect(max(article_list))

        # Analyze the whole body with langdetect
        if lang is None:
            lang = detect(root.text_content().strip())

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
