#!/usr/bin/env python
"""
This script downloads article information of one URL. The results are stored in JSON-files in a sub-folder.
You need to adapt the variables url and basepath in order to use the script.
"""

import json

from newsplease import NewsPlease

url = 'https://www.rt.com/news/203203-ukraine-russia-troops-border/'
basepath = '/Users/felix/Downloads/'

article = NewsPlease.from_url(url)

with open(basepath + article['filename'] + '.json', 'w') as outfile:
    json.dump(article, outfile, indent=4, sort_keys=True)
