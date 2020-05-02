import importlib
import inspect
import logging
from .analyzers.abstract_analyzer import AbstractAnalyzer


class Analyzer:
    """This class initializes all extractors and saves the results of them. When adding a new extractor, it needs to
    be initialized here and added to list_extractor.
    """

    def __init__(self, analyzer_list):
        """
        Initializes all the extractors, comparers and the cleaner.

        :param extractor_list: List of strings containing all extractors to be initialized.
        """
        self.log = logging.getLogger(__name__)
        self.analyzer_list = []
        for analyzer in analyzer_list:

            module = importlib.import_module(__package__ + '.analyzers.' + analyzer)

            # check module for subclasses of AbstractAnalyzer
            for member in inspect.getmembers(module, inspect.isclass):
                if issubclass(member[1], AbstractAnalyzer) and member[0] != 'AbstractAnalyzer':

                    # instantiate extractor
                    instance = getattr(module, member[0], None)()
                    if instance is not None:
                        self.log.info('Analyzer initialized: %s', analyzer)
                        self.analyzer_list.append(instance)
                    else:
                        self.log.error("Misconfiguration: An unknown Extractor was found and"
                                       " will be ignored: %s", analyzer)

    def analyze(self, item):
        """Runs the HTML-response trough a list of initialized analyzer and attached the result in a dictionary called insight.
        :param item: NewscrawlerItem to be processed.
        :return: An dictionary including the results of the analysis
        """
        analyze_result = {}
        for analyzer in self.analyzer_list:
            result = analyzer.analyze(item)
            analyze_result.update(result)
        return analyze_result
