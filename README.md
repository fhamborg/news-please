# **news-please**

news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website. news-please combines the power of multiple state-of-the-art libraries and tools such as [scrapy](https://scrapy.org/) and [newspaper](https://github.com/codelucas/newspaper).

## Features
* **works out of the box**: install with pip, add URLs of your pages, run :-)
* stores extracted information in an **ElasticSearch** index
* **easy configuration** in case you want to fine tune the extraction

## Extracted information
* headline
* lead paragraph
* main content (textual)
* main image
* author's name
* publication date

## Getting started

In this section you can find the steps to get started as quick as possible. 

Base requirements:

* [Python](https://www.python.org/downloads/) 2.7+ or 3.x
* [ElasticSearch](https://www.elastic.co/downloads/elasticsearch) 2.x

### Installation

```
#!bash

$ sudo pip install news-please
```

### Minimal configuration

If your Elasticsearch database is not located at `http://localhost:9200` or uses CA-certificate authentification you need edit the configuration file `newscrawler.cfg` at `pythonx.x/dist-packages/newsplease`:  

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


### Run the crawler

```
#!bash

$ sudo newsplease
```

news-please will start crawling pages http://www.faz.net/, http://www.zeit.de and http://www.nytimes.com/. To terminate the process simply press `CTRL+C`. news-please will then shutdown within 5-20 seconds. You can also press `CTRL+C` twice, which will immediately kill all processes. We strongly recommend to not pressing `CTRL+C` twice, though.

### What's next?

Want to crawl other websites? We've got your back! Simply go into the [`input_data.json`](https://bitbucket.org/fhamborg/news-please/wiki/user-guide#markdown-header-add-own-urls) file and add the root URLs. 
You also might want to check out our guide for the [config file](https://bitbucket.org/fhamborg/news-please/wiki/configuration). 

We have also collected a bunch of useful information for both [users](https://bitbucket.org/fhamborg/news-please/wiki/user-guide)  and [developers](https://bitbucket.org/fhamborg/news-please/wiki/developer-guide).

## Future Improvements
* Better error handling incl. more descriptive messages
* Improvement of detection whether a page is a news article or not
* New extractors
* Improve file handling, e.g support paths relative to the user: `~/data/...`

## Wiki and Documentation
You can find more information on usage and development in our [wiki](https://bitbucket.org/fhamborg/news-please/wiki/Home)!

## Credits

This project would not have been possible without the help of many students who spent time working on the extraction (ordered alphabetically):

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

You want to contribute? Great, we are always happy for any support on this project! Simply send a pull request or drop us an email: [felix.hamborg@uni-konstanz.de](felix.hamborg@uni-konstanz.de) By contributing to this project, you agree that your contributions will be licensed under the project's license (see below).

Copyright 2016 Felix Hamborg

Licensed under the [Apache License 2.0](LICENSE.txt)