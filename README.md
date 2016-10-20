# **news-please**

## Overview

news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website.

## Getting started

In this section you can find the steps to get started as quick as possible. 

Base requirements:

* [Python](https://www.python.org/downloads/) 2.7+ or 3.x
* [ElasticSearch](https://www.elastic.co/downloads/elasticsearch) 2.x

### Installation

```
#!bash

$ sudo pip install TODO
```

### Minimal configuration

TODO (what to change minimally in the config? i suppose elastic search account infos)

### Run the crawler

```
#!bash

$ python TODO
```

If everything goes well (make sure elasticsearch is running and you have added credentials in the config file of news-please) you will see the console showing the progress of crawling pages (TODO which pages). 

### What's next?

Want to crawl other websites? We've got your back! Simply go into the TODO file and add the root URLs. You also might want to check out our guide for the config file. 

We have also collected a bunch of useful information for both users (TODO link) and developers (TODO link).

## Extracted information
* headline
* lead paragraph
* main content (textual)
* main image
* author's name
* publication date

## Features
* **works out of the box**: clone the repository, add your page URLs, run :-)
* stores extracted information in an **ElasticSearch** index
* **easy configuration** in case you want to fine tune the extraction

## Future Improvements
* Better error handling incl. more descriptive messages
* Improvement of detection whether a page is a news article or not
* TODO SÖREN

## Wiki and Documentation
You can find more information on usage and development in our [wiki TODO SÖREN](TODO)!

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