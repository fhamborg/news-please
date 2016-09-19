# getthenews

getthenews is a news crawler developed by the Information Science group at the University of Konstanz. It crawls for a given root URL all subpages that are news articles. From these it automatically extracts information such headline, content, and main image. This way it enables effective download and extraction of articles from news websites.

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
* Python 2 or 3
* ElasticSearch (needs to run)

## Future Improvements
* Better error handling incl. more descriptive messages
* Improvement of detection whether a page is a news article or not

## Wiki and Documentation

You can find more information on usage and development in our [wiki TODO SÖREN](TODO)!

## License and Contribution

Please send a mail to [felix.hamborg@uni-konstanz.de](mailto:felix.hamborg@uni-konstanz.de)