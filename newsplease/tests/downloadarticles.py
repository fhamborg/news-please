import json

import os

name = 'trump-in-saudi-arabia.txt'
basepath = '/Users/felix/Downloads/'
download_dir = basepath + 'dir' + name + '/'
os.makedirs(download_dir)

articles = NewsPlease.download_from_file(basepath + name)

for url in articles:
    article = articles[url]
    with open(download_dir + article['filename'], 'w') as outfile:
        json.dump(article, outfile)

