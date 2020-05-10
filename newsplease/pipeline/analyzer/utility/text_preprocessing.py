""" Copyright 2017, Dimitrios Effrosynidis, All rights reserved. """

import re
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import string

def clean_text(text):
    ## Remove puncuation
    text = text.translate(string.punctuation)

    ## Convert words to lower case and split them
    text = text.lower().split()

    ## Remove stop words
    stops = set(stopwords.words("english"))
    text = [w for w in text if not w in stops and len(w) >= 3]

    text = " ".join(text)
    ## Clean the text
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)
    ## Stemming
    text = text.split()
    stemmer = SnowballStemmer('english')
    stemmed_words = [stemmer.stem(word) for word in text]
    text = " ".join(stemmed_words)
    return text

def removeUnicode(text):
    """ Removes unicode strings like "\u002c" and "x96" """
    text = re.sub(r'(\\u[0-9A-Fa-f]+)', r'', text)
    text = re.sub(r'[^\x00-\x7f]', r'', text)
    return text


def replaceURL(text):
    """ Replaces url address with "url" """
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'url', text)
    text = re.sub(r'#([^\s]+)', r'\1', text)
    return text


def replaceAtUser(text):
    """ Replaces "@user" with "atUser" """
    text = re.sub('@[^\s]+', 'atUser', text)
    return text


def removeHashtagInFrontOfWord(text):
    """ Removes hastag in front of a word """
    text = re.sub(r'#([^\s]+)', r'\1', text)
    return text


def removeNumbers(text):
    """ Removes integers """
    text = ''.join([i for i in text if not i.isdigit()])
    return text


def replaceMultiExclamationMark(text):
    """ Replaces repetitions of exlamation marks """
    text = re.sub(r"(\!)\1+", ' multiExclamation ', text)
    return text


def replaceMultiQuestionMark(text):
    """ Replaces repetitions of question marks """
    text = re.sub(r"(\?)\1+", ' multiQuestion ', text)
    return text


def replaceMultiStopMark(text):
    """ Replaces repetitions of stop marks """
    text = re.sub(r"(\.)\1+", ' multiStop ', text)
    return text


def countMultiExclamationMarks(text):
    """ Replaces repetitions of exlamation marks """
    return len(re.findall(r"(\!)\1+", text))


def countMultiQuestionMarks(text):
    """ Count repetitions of question marks """
    return len(re.findall(r"(\?)\1+", text))


def countMultiStopMarks(text):
    """ Count repetitions of stop marks """
    return len(re.findall(r"(\.)\1+", text))


def countElongated(text):
    """ Input: a text, Output: how many words are elongated """
    regex = re.compile(r"(.)\1{2}")
    return len([word for word in text.split() if regex.search(word)])


def countAllCaps(text):
    """ Input: a text, Output: how many words are all caps """
    return len(re.findall("[A-Z0-9]{3,}", text))


# """ Creates a dictionary with slangs and their equivalents and replaces them """
# with open('slang.txt') as file:
#     slang_map = dict(map(str.strip, line.partition('\t')[::2])
#                      for line in file if line.strip())
#
# slang_words = sorted(slang_map, key=len, reverse=True)  # longest first for regex
# regex = re.compile(r"\b({})\b".format("|".join(map(re.escape, slang_words))))
# replaceSlang = partial(regex.sub, lambda m: slang_map[m.group(1)])
#
#
# def countSlang(text):
#     """ Input: a text, Output: how many slang words and a list of found slangs """
#     slangCounter = 0
#     slangsFound = []
#     tokens = nltk.word_tokenize(text)
#     for word in tokens:
#         if word in slang_words:
#             slangsFound.append(word)
#             slangCounter += 1
#     return slangCounter, slangsFound


""" Replaces contractions from a string to their equivalents """
contraction_patterns = [(r'won\'t', 'will not'), (r'can\'t', 'cannot'), (r'i\'m', 'i am'), (r'ain\'t', 'is not'),
                        (r'(\w+)\'ll', '\g<1> will'), (r'(\w+)n\'t', '\g<1> not'),
                        (r'(\w+)\'ve', '\g<1> have'), (r'(\w+)\'s', '\g<1> is'), (r'(\w+)\'re', '\g<1> are'),
                        (r'(\w+)\'d', '\g<1> would'), (r'&', 'and'), (r'dammit', 'damn it'), (r'dont', 'do not'),
                        (r'wont', 'will not')]


def replaceContraction(text):
    patterns = [(re.compile(regex), repl) for (regex, repl) in contraction_patterns]
    for (pattern, repl) in patterns:
        (text, count) = re.subn(pattern, repl, text)
    return text


def replaceElongated(word):
    """ Replaces an elongated word with its basic form, unless the word exists in the lexicon """

    repeat_regexp = re.compile(r'(\w*)(\w)\2(\w*)')
    repl = r'\1\2\3'
    if wordnet.synsets(word):
        return word
    repl_word = repeat_regexp.sub(repl, word)
    if repl_word != word:
        return replaceElongated(repl_word)
    else:
        return repl_word


def removeEmoticons(text):
    """ Removes emoticons from text """
    text = re.sub(
        ':\)|;\)|:-\)|\(-:|:-D|=D|:P|xD|X-p|\^\^|:-*|\^\.\^|\^\-\^|\^\_\^|\,-\)|\)-:|:\'\(|:\(|:-\(|:\S|T\.T|\.\_\.|:<|:-\S|:-<|\*\-\*|:O|=O|=\-O|O\.o|XO|O\_O|:-\@|=/|:/|X\-\(|>\.<|>=\(|D:',
        '', text)
    return text


def countEmoticons(text):
    """ Input: a text, Output: how many emoticons """
    return len(re.findall(
        ':\)|;\)|:-\)|\(-:|:-D|=D|:P|xD|X-p|\^\^|:-*|\^\.\^|\^\-\^|\^\_\^|\,-\)|\)-:|:\'\(|:\(|:-\(|:\S|T\.T|\.\_\.|:<|:-\S|:-<|\*\-\*|:O|=O|=\-O|O\.o|XO|O\_O|:-\@|=/|:/|X\-\(|>\.<|>=\(|D:',
        text))

def replace(word, pos=None):
    """ Creates a set of all antonyms for the word and if there is only one antonym, it returns it """
    antonyms = set()
    for syn in wordnet.synsets(word, pos=pos):
        for lemma in syn.lemmas():
            for antonym in lemma.antonyms():
                antonyms.add(antonym.name())
    if len(antonyms) == 1:
        return antonyms.pop()
    else:
        return None


def replaceNegations(text):
    """ Finds "not" and antonym for the next word and if found, replaces not and the next word with the antonym """
    i, l = 0, len(text)
    words = []
    while i < l:
        word = text[i]
        if word == 'not' and i + 1 < l:
            ant = replace(text[i + 1])
            if ant:
                words.append(ant)
                i += 2
                continue
        words.append(word)
        i += 1
    return words


### Replace Negations End ###

def addNotTag(text):
    """ Finds "not,never,no" and adds the tag NEG_ to all words that follow until the next punctuation """
    transformed = re.sub(r'\b(?:not|never|no)\b[\w\s]+[^\w\s]',
                         lambda match: re.sub(r'(\s+)(\w+)', r'\1NEG_\2', match.group(0)),
                         text,
                         flags=re.IGNORECASE)
    return transformed


def addCapTag(word):
    """ Finds a word with at least 3 characters capitalized and adds the tag ALL_CAPS_ """
    if (len(re.findall("[A-Z]{3,}", word))):
        word = word.replace('\\', '')
        transformed = re.sub("[A-Z]{3,}", "ALL_CAPS_" + word, word)
        return transformed
    else:
        return word

def test():
    text = "Offering an article's reading time estimation to your site's content, can contribute greatly to your end users." \
           "  First of all, it allows end users to prepare the time they needs to read an article in full. Secondly," \
           " it could help them choose the right article for the right amount of available time they have." \
           " Lastly, it opens a whole new range of features, sorting options and filter improvements you can offer (like" \
           " filtering articles by reading time). From http://www.assafelovic.com/blog/2017/6/27/estimating-an-articles-reading-time @BryanChen"
    addCapTag(text)
    addNotTag(text)
    replaceNegations(text)
    countEmoticons(text)
    removeEmoticons(text)
    removeUnicode(text)
    replaceURL(text)
    replaceAtUser(text)
    removeHashtagInFrontOfWord(text)
    removeNumbers(text)
    replaceMultiExclamationMark(text)
    replaceMultiQuestionMark(text)
    replaceMultiStopMark(text)
    countMultiExclamationMarks(text)
    countMultiQuestionMarks(text)
    countMultiStopMarks(text)
    text = clean_text(text)
    print(text)

if __name__ == "__main__":
    test()