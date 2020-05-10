from nltk.tokenize import word_tokenize, sent_tokenize
from textblob import  TextBlob
from ..utility.text_preprocessing import clean_text
from .abstract_analyzer import AbstractAnalyzer
import numpy as np
'''
Argument:
    text: a long string
    cleaned: indicating whether the text has been preprocessed or not
'''

class SimpleAnalyzer(AbstractAnalyzer):

    # average minseconds per word, source: https://www.forbes.com/sites/brettnelson/2012/06/04/do-you-read-fast-enough-to-be-successful/#7ef6c8f6462e
    AMPW =300

    def get_result(self, item):
        insight = {}
        text = item['article_text']
        if not text:
            return insight
        else:
            text = self.single_text_preprocessing(text)
            insight = self.single_analyze(text)
        return insight

    def single_text_preprocessing(self, text):
        text = clean_text(text)
        return text

    def single_analyze(self, text):
        text = self.single_text_preprocessing(text)
        insight = {'polarity':0.0, 'subjectivity': 0.0, 'reading_time': 0, 'words_count':0}
        insight['polarity'], insight['subjectivity'] = self.text_blob_scoring(text)
        insight['reading_time'], insight['words_count'] = self.estimate_reading_time(text)
        return insight

    def text_blob_scoring(self, text):
        polarity_scores = []
        subjectivity_scores = []
        blob = TextBlob(text)
        for sent in blob.sentences:
            polarity_scores.append(sent.sentiment.polarity)
            subjectivity_scores.append(sent.sentiment.subjectivity)
        p_avg = round(np.mean(polarity_scores), 2)
        s_avg = round(np.mean(subjectivity_scores), 2)
        return p_avg, s_avg

    def estimate_reading_time(self, text):
        text = clean_text(text)
        words = word_tokenize(text)
        est_reading_ms = self.AMPW*len(words)
        return round(est_reading_ms/1000), len(words)