# **news-please** 

<img align="right" height="128px" width"128px" src="/misc/logo/logo-256.png" /> news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website. news-please combines the power of multiple state-of-the-art libraries and tools such as [scrapy](https://scrapy.org/), [Newspaper](https://github.com/codelucas/newspaper), and [readability](https://github.com/buriy/python-readability). 

## Extracted information
* headline
* lead paragraph
* main content (textual)
* main image
* author's name
* publication date
* language

## Features
* **works out of the box**: install with pip, add URLs of your pages, run :-)
* execute it conveniently with the **CLI** or use it as a **library** within your own software
* runs on your favorite Python version (2.7+ and 3+)

### CLI mode
* stores extracted results in **JSON files or ElasticSearch** (other storages can be added easily)
* **simple but extensive configuration** (if you want to tweak the results)
* revisions: crawl articles multiple times and track changes

### Library mode
* crawl and extract information for a list of article URLs (currently the fullsite-crawling is only supported via the CLI)

## Getting started

It's super easy, we promise!

### Installation

```
$ sudo pip install news-please
```

### Use within your own code (as a library)
```python
from newsplease import NewsPlease
article = NewsPlease.download_article('https://www.nytimes.com/2017/02/23/us/politics/cpac-stephen-bannon-reince-priebus.html?hp')
print(article['title'])
```
or if you want to crawl multiple articles at a time
```python
NewsPlease.download_articles([url1, url2, ...])
```

### Run the crawler (via the CLI)

```
$ news-please
```

news-please will then start crawling a few examples pages. To terminate the process simply press `CTRL+C`. news-please will then shutdown within 5-60 seconds. You can also press `CTRL+C` twice, which will immediately kill the process (not recommended, though).

The results are stored by default in JSON files in the `data` folder. In the default configuration, news-please also stores the original HTML files.

### Crawl other pages

Of course, you want to crawl other websites. Simply go into the [`sitelist.hjson`](https://github.com/fhamborg/news-please/wiki/user-guide#sitelisthjson) file and add the root URLs of the news outlets' webpages of your choice. 

### ElasticSearch

news-please also supports export to ElasticSearch. Using Elasticsearch will also enable the versioning feature. First, enable it in the [`config.cfg`](https://github.com/fhamborg/news-please/wiki/configuration) at the config directory, which is by default `~/news-please/config` but can be changed also with the `-c` parameter to a custom location. In case the directory does not exist, a default directory will be created at the specified location.

    [Scrapy]
    
    ITEM_PIPELINES = {
                       'newscrawler.pipeline.pipelines.ElasticSearchStorage':350
                     }

That's it! Except, if your Elasticsearch database is not located at `http://localhost:9200`, uses a different username / password or CA-certificate authentication. In these cases, you will also need to change the following.

    [Elasticsearch]

    host = localhost
    port = 9200	

    ...

    # Credentials used  for authentication (supports CA-certificates):
	
    use_ca_certificates = False'           #If True authentification is performed 
    ca_cert_path = '/path/to/cacert.pem'  
    client_cert_path = '/path/to/client_cert.pem'  
    client_key_path = '/path/to/client_key.pem'  
    username = 'root'  
    secret = 'password' 

### What's next?

We have collected a bunch of useful information for both [users](https://github.com/fhamborg/news-please/wiki/user-guide)  and [developers](https://github.com/fhamborg/news-please/wiki/developer-guide). As a user, you will most likely only deal with two files: [`sitelist.hjson`](https://github.com/fhamborg/news-please/wiki/user-guide#sitelisthjson) (to define sites to be crawled) and [`config.cfg`](https://github.com/fhamborg/news-please/wiki/configuration) (probably only rarely, in case you want to tweak the configuration).

## Future improvements
* Better error handling incl. more descriptive messages
* Better logging (currently, we think that the logging is either too detailed or too silent)
* Improvement of detection whether a page is a news article or not

## Wiki and documentation
You can find more information on usage and development in our [wiki](https://github.com/fhamborg/news-please/wiki)!

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

## How to cite
If you are using news-please, please cite our [paper](http://www.gipp.com/wp-content/papercite-data/pdf/hamborg2017.pdf):
```
@InProceedings{Hamborg2017,
  author     = {{H}amborg, {F}elix and {M}euschke, {N}orman and {B}reitinger, {C}orinna and {G}ipp, {B}ela},
  title      = {{news-please}: {A} {G}eneric {N}ews {C}rawler and {E}xtractor},
  year       = {2017},
  booktitle  = {{P}roceedings of the 15th {I}nternational {S}ymposium of {I}nformation {S}cience},
  location   = {Berlin},
}
```

## Contribution
You want to contribute? Great, we are always happy for any support on this project! Simply send a pull request or drop us an email: [felix.hamborg@uni-konstanz.de](felix.hamborg@uni-konstanz.de). By contributing to this project, you agree that your contributions will be licensed under the project's license (see below).

## License
The project is licensed under the [Apache License 2.0](LICENSE.txt). Make sure that you use news-please in compliance with applicable law. The news-please logo is courtesy of Mario Hamborg.

Copyright 2016 [Felix Hamborg](http://felix.hamborg.eu/)
