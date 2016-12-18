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
* **works out of the box**: install with pip, add URLs of your pages, run :-)
* stores extracted results in **JSON files or ElasticSearch** (other storages can be added easily)
* **simple but extensive configuration** (if you want to tweak the results)
* runs on your favorite Python version (2.7+ and 3+)
* revisions: crawl articles multiple times and track changes

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

$ news-please
```

news-please will then start crawling a few examples pages. To terminate the process simply press `CTRL+C`. news-please will then shutdown within 5-60 seconds. You can also press `CTRL+C` twice, which will immediately kills the process (not recommended, though).

The results are stored by default in JSON files in the `data` folder. 

### Crawl other pages

Of course, you want to crawl other websites. Simply go into the [`sitelist.hjson`](https://bitbucket.org/fhamborg/news-please/wiki/user-guide#markdown-header-add-own-urls) file and add the root URLs of the news outlets' webpages of your choice. 

### ElasticSearch

news-please also supports export to ElasticSearch. Using Elasticsearch will also enable the versioning feature. First, enable it in the [`config.cfg`](https://bitbucket.org/fhamborg/news-please/wiki/configuration) at the config directory, which is by default `~/news-please/config` but can be changed also with the `-c` parameter to a custom location. In case the directory does not exist, a default directory will be created at the specified location.

    [Scrapy]
    
    ITEM_PIPELINES = {'newscrawler.pipeline.pipelines.ArticleMasterExtractor':100,
                  'newscrawler.pipeline.pipelines.LocalStorage':200,
                  'newscrawler.pipeline.pipelines.ElasticSearchStorage':350
                  }

That's it! Except, if your Elasticsearch database is not located at `http://localhost:9200`, uses a different username / password or CA-certificate authentication. In these cases, you will also need to change the following.

    [Elasticsearch]

    host = localhost
    port = 9200	

    ...

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
* Better logging (currently, we think that the logging is either too detailed or too silent)
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

## Usage, License, Contribution and Contact

Make sure that you use news-please in compliance with applicable law. 

You want to contribute? Great, we are always happy for any support on this project! Simply send a pull request or drop us an email: [felix.hamborg@uni-konstanz.de](felix.hamborg@uni-konstanz.de). By contributing to this project, you agree that your contributions will be licensed under the project's license (see below).

The project is licensed under the [Apache License 2.0](LICENSE.txt). If you're using news-please and find it a useful tool (or not), please let us know. The news-please logo is courtesy of [Mario Hamborg](http://mario.hamborg.eu/).

Copyright 2016 [Felix Hamborg](http://felix.hamborg.eu/)