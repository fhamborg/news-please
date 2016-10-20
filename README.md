# **news-please**

news-please is an easy-to-use news crawler that can download and extract structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website.

## Extracted Information
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

## Requirements
* [Python](https://www.python.org/downloads/) 2.7+ or 3.x
* [ElasticSearch](https://www.elastic.co/downloads/elasticsearch) (needs to run)

## Future Improvements
* Better error handling incl. more descriptive messages
* Improvement of detection whether a page is a news article or not
* TODO SÖREN

## Wiki and Documentation
You can find more information on usage and development in our [wiki TODO SÖREN](TODO)!

## Acknoledgements
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

You want to contribute? Great, we are always happy for any support on this project! Simply send a pull request or drop us an email: felix.hamborg (at) uni-konstanz.de

Copyright 2016 Felix Hamborg

Licensed under the [Apache License 2.0](LICENSE.txt)