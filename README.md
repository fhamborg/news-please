# **news-please** #

## Announcement
If you're interested in news analysis, you might also want to check out our new project, [Giveme5W1H](https://github.com/fhamborg/Giveme5W1H) - a tool that extracts phrases answering the journalistic five W and one H questions to describe an article's main event, i.e., who did what, when, where, why, and how.
 
[![PyPI version](https://badge.fury.io/py/news-please.svg)](https://badge.fury.io/py/news-please)

<img align="right" height="128px" width="128px" src="https://raw.githubusercontent.com/fhamborg/news-please/master/misc/logo/logo-256.png" /> 

news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website. news-please combines the power of multiple state-of-the-art libraries and tools, such as [scrapy](https://scrapy.org/), [Newspaper](https://github.com/codelucas/newspaper), and [readability](https://github.com/buriy/python-readability). news-please also features a library mode, which allows developers to use the crawling and extraction functionality within their own program. Moreover, news-please allows to conveniently [crawl and extract articles](https://github.com/fhamborg/news-please/blob/master/newsplease/examples/commoncrawl.py) from commoncrawl.org.

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
* run news-please conveniently with the **CLI** or use it as a **library** within your own software or to extract articles from **the news archive of commoncrawl.org**
* runs on your favorite Python version (2.7 and 3+)

### Modes and use cases
news-please supports three use cases, which are explained in more detail in the following.

#### CLI mode
* stores extracted results in **JSON files or ElasticSearch** (you can implement other storages easily)
* **simple but extensive configuration** (if you want to tweak the results)
* revisions: crawl articles multiple times and track changes

#### Library mode
* crawl and extract information given a list of article URLs
* to use news-please within your own Python code

#### News archive from commoncrawl.org
* commoncrawl.org provides an extensive, free-to-use archive of news articles from small and major publishers world wide
* news-please enables users to conveniently download and extract articles from commoncrawl.org
* you can optionally define filter criteria, such as news publisher(s) or the date period, within which articles need to be published
* clone the news-please repository, adapt the config section in [newsplease/examples/commoncrawl.py](https://github.com/fhamborg/news-please/blob/master/newsplease/examples/commoncrawl.py), and execute `python3 -m newsplease.examples.commoncrawl`

## Getting started
It's super easy, we promise!

### Installation
We prefer Python 3, but Python 2.7 is supported, too!
```
$ pip3 install news-please 
```

### Use within your own code (as a library)
You can access the core functionality of news-please, i.e. extraction of semi-structured information from one or more news articles, in your own code by using news-please in library mode. If you want to use news-please's full website extraction (given only the root URL) or continuous crawling mode (using RSS), you'll need to use the CLI mode.
```python
from newsplease import NewsPlease
article = NewsPlease.from_url('https://www.nytimes.com/2017/02/23/us/politics/cpac-stephen-bannon-reince-priebus.html?hp')
print(article.title)
```
A sample of an extracted article can be found [here (as a JSON file)](https://github.com/fhamborg/news-please/blob/master/newsplease/examples/sample.json).

If you want to crawl multiple articles at a time, optionally with a timeout in seconds
```python
NewsPlease.from_urls([url1, url2, ...], timeout=6)
```
or if you have a file containing all URLs (each line containing a single URL)
```python
NewsPlease.from_file(path)
```
or if you have raw HTML data (you can also provide the original URL to increase the accuracy of extracting the correct publishing date)
```python
NewsPlease.from_html(html, url=None) 
```
or if you have a [WARC file](https://github.com/webrecorder/warcio) (also check out our [commoncrawl workflow](https://github.com/fhamborg/news-please/blob/master/newsplease/examples/commoncrawl.py), which provides convenient methods to filter commoncrawl's archive for specific hosts and dates)
```
NewsPlease.from_warc(warc_record)
```
In library mode, news-please will attempt to download and extract information from each URL. The previously described functions are blocking, i.e., will return once news-please has attempted all URLs. The resulting list contains all successfully extracted articles.

### Run the crawler (via the CLI)

```
$ news-please
```

news-please will then start crawling a few examples pages. To terminate the process press `CTRL+C`. news-please will then shut down within 5-60 seconds. You can also press `CTRL+C` twice, which will immediately kill the process (not recommended, though).

The results are stored by default in JSON files in the `data` folder. In the default configuration, news-please also stores the original HTML files.

### Crawl other pages

Most likely, you will not want to crawl from the websites provided in our example configuration. Simply head ofer to the [`sitelist.hjson`](https://github.com/fhamborg/news-please/wiki/user-guide#sitelisthjson) file and add the root URLs of the news outlets' web pages of your choice. 

### ElasticSearch

news-please also supports export to ElasticSearch. Using Elasticsearch will also enable the versioning feature. First, enable it in the [`config.cfg`](https://github.com/fhamborg/news-please/wiki/configuration) at the config directory, which is by default `~/news-please/config` but can also be changed with the `-c` parameter to a custom location. In case the directory does not exist, a default directory will be created at the specified location.

    [Scrapy]
    
    ITEM_PIPELINES = {
                       'newsplease.pipeline.pipelines.ArticleMasterExtractor':100,
                       'newsplease.pipeline.pipelines.ElasticsearchStorage':350
                     }

That's it! Except, if your Elasticsearch database is not located at `http://localhost:9200`, uses a different username/password or CA-certificate authentication. In these cases, you will also need to change the following.

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

## Wiki and support (also, how to open an issue)
You can find more information on usage and development in our [wiki](https://github.com/fhamborg/news-please/wiki)! Before contacting us, please check out the wiki. If you still have questions on how to use news-please, please create a new [issue](https://github.com/fhamborg/news-please/issues) on GitHub. 
### Issues
Make sure to include information about your Python version, operating system, which version of news-please you are running (make sure it is the latest, no support for older versions), and how you use news-please (installed via pip or git clone).

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

We also thank all other contributors, which you can find on the [contributors' page](https://github.com/fhamborg/news-please/graphs/contributors)!

## How to cite
If you are using news-please, please cite our [paper](http://www.gipp.com/wp-content/papercite-data/pdf/hamborg2017.pdf) ([ResearchGate](https://www.researchgate.net/publication/314072045_news-please_A_Generic_News_Crawler_and_Extractor), [Mendeley](https://www.mendeley.com/research-papers/newsplease-generic-news-crawler-extractor/)):
```
@InProceedings{Hamborg2017,
  author     = {Hamborg, Felix and Meuschke, Norman and Breitinger, Corinna and Gipp, Bela},
  title      = {news-please: A Generic News Crawler and Extractor},
  year       = {2017},
  booktitle  = {Proceedings of the 15th International Symposium of Information Science},
  location   = {Berlin},
  editor     = {Gaede, Maria and Trkulja, Violeta and Petra, Vivien},
  pages      = {218--223},
  month      = {March}
}
```
You can find more information on this and other news projects on our [website](https://felix.hamborg.eu/).

## Contribution and custom features
Do you want to contribute? Great, we are always happy for any support on this project! Just send a pull request. By contributing to this project, you agree that your contributions will be licensed under the project's license (see below). If you have questions or issues while working on the code, e.g., when implementing a new feature that you would like to have added to news-please, open an issue on GitHub and we'll be happy to help you. Please note that we usually do not have enough resources to implement features requested by users - instead we recommend to implement them yourself, and send a pull request. 

## License
Licensed under the Apache License, Version 2.0 (the "License"); you may not use news-please except in compliance with the License. A copy of the License is included in the project, see the file [LICENSE.txt](LICENSE.txt).

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License. The news-please logo is courtesy of [Mario Hamborg](https://mario.hamborg.eu/). 

Copyright 2016-2018 The news-please team
