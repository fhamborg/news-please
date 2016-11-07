# **news-please**

news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website. news-please combines the power of multiple state-of-the-art libraries and tools such as [scrapy](https://scrapy.org/), [Newspaper](https://github.com/codelucas/newspaper), and [readability](https://github.com/buriy/python-readability).

## Extracted information
* headline
* lead paragraph
* main content (textual)
* main image
* author's name
* publication date

## Features
* works out of the box: install with pip, add URLs of your pages, run :-)
* stores extracted results in JSON files or ElasticSearch (other storages can be added easily)
* simple but extensive configuration (if you want to tweak the results)
* runs on Python 2.7 (and later) and 3
* versioning: crawl articles multiple times and track changes

## Getting started

It's super easy, we promise!

### Installation

```
#!bash

$ sudo pip install news-please
```

### Run the crawler

```
#!bash

$ newsplease
```

news-please will then start crawling a few examples pages. To terminate the process simply press `CTRL+C`. news-please will then shutdown within 5-60 seconds. You can also press `CTRL+C` twice, which will immediately kill all processes (not recommended, though).

The results are stored by default in JSON files in the `data` folder. 

### Add your own pages

Want to crawl other websites? We've got your back! Simply go into the [`sitelist.hjson`](https://bitbucket.org/fhamborg/news-please/wiki/user-guide#markdown-header-add-own-urls) file and add the root URLs. 

### ElasticSearch

news-please also supports export to ElasticSearch. Using Elasticsearch will also enable the versioning feature. First, enable it in the `config.cfg` at `pythonx.x/dist-packages/newsplease`:

    [Scrapy]
    
    ITEM_PIPELINES = {'newscrawler.pipeline.pipelines.ArticleMasterExtractor':100,
                  'newscrawler.pipeline.pipelines.LocalStorage':200,
                  'newscrawler.pipeline.pipelines.ElasticSearchStorage':350
                  }

That's it! Except, if your Elasticsearch database is not located at `http://localhost:9200`, uses a different username / password or CA-certificate authentication you will also need to change the following.

    [Elasticsearch]

    host = localhost
    port = 9200	

    #The indices used to store the extracted meta-data:

    index_current = 'news-please'
    index_archive = 'news-please-archive'

    #Credentials used  for authentication (supports CA-certificates):
	
    use_ca_certificates = False'           #If True authentification is performed 
    ca_cert_path = '/path/to/cacert.pem'  
    client_cert_path = '/path/to/client_cert.pem'  
    client_key_path = '/path/to/client_key.pem'  
    username = 'root'  
    secret = 'password' 

### What's next?

We have collected a bunch of useful information for both [users](https://bitbucket.org/fhamborg/news-please/wiki/user-guide)  and [developers](https://bitbucket.org/fhamborg/news-please/wiki/developer-guide). As a user, you will most likely only deal with two files: the [`config.cfg`](https://bitbucket.org/fhamborg/news-please/wiki/configuration) and the [`sitelist.hjson`](https://bitbucket.org/fhamborg/news-please/wiki/user-guide#markdown-header-add-own-urls).

## Future Improvements
* Better error handling incl. more descriptive messages
* Better logging
* Improvement of detection whether a page is a news article or not

## Wiki and Documentation
You can find more information on usage and development in our [wiki](https://bitbucket.org/fhamborg/news-please/wiki/Home)!

## Acknowledgements

This project would not have been possible without the contributions of the following students (ordered alphabetically):

* Moritz Bock
* Michael Fried
* Jonathan Hassler
* Markus Klatt
* Kevin Kress
* Sören Lachnit
* Marvin Pafla
* Franziska Schlor
* Matt Sharinghousen
* Claudio Spener
* Moritz Steinmaier

## License and Contribution

You want to contribute? Great, we are always happy for any support on this project! Simply send a pull request or drop us an email: [felix.hamborg@uni-konstanz.de](felix.hamborg@uni-konstanz.de). By contributing to this project, you agree that your contributions will be licensed under the project's license (see below).

Copyright 2016 Felix Hamborg

Licensed under the [Apache License 2.0](LICENSE.txt)