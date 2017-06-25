# **news-please** #

[![PyPI version](https://badge.fury.io/py/news-please.svg)](https://badge.fury.io/py/news-please)

<img align="right" height="128px" width="128px" src="https://raw.githubusercontent.com/fhamborg/news-please/master/misc/logo/logo-256.png" /> 

news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website. news-please combines the power of multiple state-of-the-art libraries and tools, such as [scrapy](https://scrapy.org/), [Newspaper](https://github.com/codelucas/newspaper), and [readability](https://github.com/buriy/python-readability). news-please also features a library mode, which allows developers to use the crawling and extraction functionality within their own program.

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
* crawl and extract information for a list of article URLs. 

## Getting started

It's super easy, we promise!

### Installation

```
$ pip install news-please
```

### Use within your own code (as a library)
If you want to use news-please's full website extraction or continuous crawling mode (using RSS), you need to use the CLI mode as the library mode does only support single URL extraction.
```python
from newsplease import NewsPlease
article = NewsPlease.from_url('https://www.nytimes.com/2017/02/23/us/politics/cpac-stephen-bannon-reince-priebus.html?hp')
print(article.title)
```
A sample of an extracted article can be found [here (as a JSON file)](https://github.com/fhamborg/news-please/blob/master/newsplease/examples/sample.json).

or if you want to crawl multiple articles at a time
```python
NewsPlease.from_urls([url1, url2, ...])
```
or if you have a file containing all URLs (each line containing a single URL)
```python
NewsPlease.from_file(path)
```
or if you have a [WARC file](https://github.com/webrecorder/warcio) 
```
NewsPlease.from_warc(warc_record)
```
In library mode, news-please will attempt to download and extract information from each URL. The previously described functions are blocking, i.e. will return once all URLs have been attempted. The resulting list contains all articles that have been extracted successfully.

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
                       'newsplease.pipeline.pipelines.ArticleMasterExtractor':100,
                       'newsplease.pipeline.pipelines.ElasticsearchStorage':350
                     }

That's it! Except, if your Elasticsearch database is not located at `http://localhost:9200`, uses a different username / password or CA-certificate authentication. In these cases, you will also need to change the following.

    [Elasticsearch]

    host = localhost
    port = 9200	

    ...

    # Credentials used  for authentication (supports CA-certificates):
	
    use_ca_certificates = False           # True if authentification needs to be performed 
    ca_cert_path = '/path/to/cacert.pem'  
    client_cert_path = '/path/to/client_cert.pem'  
    client_key_path = '/path/to/client_key.pem'  
    username = 'root'  
    secret = 'password' 

### What's next?

We have collected a bunch of useful information for both [users](https://github.com/fhamborg/news-please/wiki/user-guide)  and [developers](https://github.com/fhamborg/news-please/wiki/developer-guide). As a user, you will most likely only deal with two files: [`sitelist.hjson`](https://github.com/fhamborg/news-please/wiki/user-guide#sitelisthjson) (to define sites to be crawled) and [`config.cfg`](https://github.com/fhamborg/news-please/wiki/configuration) (probably only rarely, in case you want to tweak the configuration).

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
If you are using news-please, please cite our [paper](http://www.gipp.com/wp-content/papercite-data/pdf/hamborg2017.pdf) ([ResearchGate](https://www.researchgate.net/publication/314072045_news-please_A_Generic_News_Crawler_and_Extractor)):
```
@InProceedings{Hamborg2017,
  author     = {{H}amborg, {F}elix and {M}euschke, {N}orman and {B}reitinger, {C}orinna and {G}ipp, {B}ela},
  title      = {{news-please}: {A} {G}eneric {N}ews {C}rawler and {E}xtractor},
  year       = {2017},
  booktitle  = {{P}roceedings of the 15th {I}nternational {S}ymposium of {I}nformation {S}cience},
  location   = {Berlin},
  editor     = {Gaede, Maria and Trkulja, Violeta and Petra, Vivien},
  pages      = {218--223},
  month      = {March}
}
```
You can find more information on this and other news projects on our [website](https://felix.hamborg.eu/).

## Contribution
You want to contribute? Great, we are always happy for any support on this project! Simply send a pull request or drop us an email: [felix.hamborg@uni-konstanz.de](felix.hamborg@uni-konstanz.de). By contributing to this project, you agree that your contributions will be licensed under the project's license (see below).

## License
The project is licensed under the [Apache License 2.0](LICENSE.txt). Make sure that you use news-please in compliance with applicable law. The news-please logo is courtesy of [Mario Hamborg](https://mario.hamborg.eu/). 

Copyright 2016 The news-please team
