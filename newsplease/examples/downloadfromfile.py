#!/usr/bin/env python
"""
This script reads in URLs from a text-file "name" and downloads article information for each of URLs. The results
are stored in JSON-files in a sub-folder. You need to adapt the variables name and basepath in order to use the
script.
"""

import json

import os

from newsplease import NewsPlease

name = 'trump-in-saudi-arabia.txt'
basepath = '/Users/felix/Downloads/'

download_dir = basepath + 'dir' + name + '/'
os.makedirs(download_dir)

articles = NewsPlease.from_file(basepath + name)

for url in articles:
    article = articles[url]
    with open(download_dir + article['filename'] + '.json', 'w') as outfile:
        json.dump(article, outfile, indent=4, sort_keys=True)
