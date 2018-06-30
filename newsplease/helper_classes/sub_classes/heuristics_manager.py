import logging
import re

try:
    basestring = basestring
except NameError:
    basestring = (str, bytes)


class HeuristicsManager(object):
    """
    This class is for managing the heuristics of
    a heuristics file (../heuristics.py)
    and adding the methods needed to check the heuristic (is_article).

    The heuristics file must inherit this class.

    The config is provided in self.cfg_heuristics,
    and logging is provided in self.log.
    """
    cfg_heuristics = None
    log = None

    __sites_object = {}
    __sites_heuristics = {}
    __heuristics_condition = None
    __condition_allowed = ["(", ")", " and ", " or ", " not "]

    def __init__(self, cfg_heuristics, sites_object, crawler_class):
        self.cfg_heuristics = cfg_heuristics
        for site in sites_object:
            self.__sites_object[site["url"]] = site
        self.log = logging.getLogger(__name__)
        self.crawler_class = crawler_class

    def is_article(self, response, url):
        """
        Tests if the given response is an article by calling and checking
        the heuristics set in config.cfg and sitelist.json

        :param obj response: The response of the site.
        :param str url: The base_url (needed to get the site-specific config
                        from the JSON-file)
        :return bool: true if the heuristics match the site as an article
        """
        site = self.__sites_object[url]
        heuristics = self.__get_enabled_heuristics(url)

        self.log.info("Checking site: %s", response.url)

        statement = self.__get_condition(url)
        self.log.debug("Condition (original): %s", statement)

        for heuristic, condition in heuristics.items():
            heuristic_func = getattr(self, heuristic)
            result = heuristic_func(response, site)
            check = self.__evaluate_result(result, condition)
            statement = re.sub(r"\b%s\b" % heuristic, str(check), statement)

            self.log.debug("Checking heuristic (%s)"
                           " result (%s) on condition (%s): %s",
                           heuristic, result, condition, check)

        self.log.debug("Condition (evaluated): %s", statement)
        is_article = eval(statement)
        self.log.debug("Article accepted: %s", is_article)
        return is_article

    def __get_condition(self, url):
        """
        Gets the condition for a url and validates it.

        :param str url: The url to get the condition for
        """
        if self.__heuristics_condition is not None:
            return self.__heuristics_condition
        if "pass_heuristics_condition" in self.__sites_object[url]:
            condition = \
                self.__sites_object[url]["pass_heuristics_condition"]
        else:
            condition = \
                self.cfg_heuristics["pass_heuristics_condition"]

        # Because the condition will be eval-ed (Yeah, eval is evil, BUT only
        # when not filtered properly), we are filtering it here.
        # Anyway, if that filter-method is not perfect: This is not any
        # random user-input thats evaled. This is (hopefully still when you
        # read this) not a webtool, where you need to filter everything 100%
        # properly.
        disalloweds = condition
        heuristics = self.__get_enabled_heuristics(url)

        for allowed in self.__condition_allowed:
            disalloweds = disalloweds.replace(allowed, " ")

        for heuristic, _ in heuristics.items():
            disalloweds = re.sub(r"\b%s\b" % heuristic, " ", disalloweds)

        disalloweds = disalloweds.split(" ")
        for disallowed in disalloweds:
            if disallowed != "":
                self.log.error("Misconfiguration: In the condition,"
                               " an unknown heuristic was found and"
                               " will be ignored: %s", disallowed)
                condition = re.sub(r"\b%s\b" % disallowed, "True", condition)

        self.__heuristics_condition = condition
        # Now condition should just consits of not, and, or, (, ), and all
        # enabled heuristics.
        return condition

    def __evaluate_result(self, result, condition):
        """
        Evaluates a result of a heuristic
        with the condition given in the config.

        :param mixed result: The result of the heuristic
        :param mixed condition: The condition string to evaluate on the result
        :return bool: Whether the heuristic result matches the condition
        """

        # If result is bool this means, that the heuristic
        # is bool as well or has a special situation
        # (for example some condition [e.g. in config] is [not] met, thus
        #  just pass it)
        if isinstance(result, bool):
            return result

        # Check if the condition is a String condition,
        # allowing <=, >=, <, >, = conditions or string
        # when they start with " or '
        if isinstance(condition, basestring):

            # Check if result should match a string
            if (condition.startswith("'") and condition.endswith("'")) or \
                    (condition.startswith('"') and condition.endswith('"')):
                if isinstance(result, basestring):
                    self.log.debug("Condition %s recognized as string.",
                                   condition)
                    return result == condition[1:-1]
                return self.__evaluation_error(
                    result, condition, "Result not string")

            # Only number-comparision following
            if not isinstance(result, (float, int)):
                return self.__evaluation_error(
                    result, condition, "Result not number on comparision")

            # Check if result should match a number
            if condition.startswith("="):
                number = self.__try_parse_number(condition[1:])
                if isinstance(number, bool):
                    return self.__evaluation_error(
                        result, condition, "Number not parsable (=)")
                return result == number

            # Check if result should be >= then a number
            if condition.startswith(">="):
                number = self.__try_parse_number(condition[2:])
                if isinstance(number, bool):
                    return self.__evaluation_error(
                        result, condition, "Number not parsable (>=)")
                return result >= number

            # Check if result should be <= then a number
            if condition.startswith("<="):
                number = self.__try_parse_number(condition[2:])
                if isinstance(number, bool):
                    return self.__evaluation_error(
                        result, condition, "Number not parsable (<=)")
                return result <= number

            # Check if result should be > then a number
            if condition.startswith(">"):
                number = self.__try_parse_number(condition[1:])
                if isinstance(number, bool):
                    return self.__evaluation_error(
                        result, condition, "Number not parsable (>)")
                return result > number

            # Check if result should be < then a number
            if condition.startswith("<"):
                number = self.__try_parse_number(condition[1:])
                if isinstance(number, bool):
                    return self.__evaluation_error(
                        result, condition, "Number not parsable (<)")
                return result < number

            # Check if result should be equal a number
            number = self.__try_parse_number(condition)
            if isinstance(number, bool):
                return self.__evaluation_error(
                    result, condition, "Number not parsable")
            return result == number

        # Check if the condition is a number and matches the result
        if isinstance(condition, (float, int)) and isinstance(result, (float, int)):
            return condition == result

        return self.__evaluation_error(result, condition, "Unknown")

    def __evaluation_error(self, result, condition, throw):
        """Helper-method for easy error-logging"""
        self.log.error("Result does not match condition, dropping item. "
                       "Result %s; Condition: %s; Throw: %s",
                       result, condition, throw)
        return False

    def __try_parse_number(self, string):
        """Try to parse a string to a number, else return False."""
        try:
            return int(string)
        except ValueError:
            try:
                return float(string)
            except ValueError:
                return False

    def __get_enabled_heuristics(self, url):
        """
        Get the enabled heuristics for a site, merging the default and the
        overwrite together.
        The config will only be read once and the merged site-config will be
        cached.

        :param str url: The url to get the heuristics for.
        """
        if url in self.__sites_heuristics:
            return self.__sites_heuristics[url]

        site = self.__sites_object[url]
        heuristics = dict(self.cfg_heuristics["enabled_heuristics"])
        if "overwrite_heuristics" in site:
            for heuristic, value in site["overwrite_heuristics"].items():
                if value is False and heuristic in heuristics:
                    del heuristics[heuristic]
                else:
                    heuristics[heuristic] = value
        self.__sites_heuristics[site["url"]] = heuristics

        self.log.debug(
            "Enabled heuristics for %s: %s", site["url"], heuristics
        )

        return heuristics
