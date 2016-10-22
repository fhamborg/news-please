-- Re-initalize DB-schema for the news-please web-crawler
-- Updated: 03.07.2016 15:20

--
-- Table structure for table `ArchiveVersions`
--

DROP TABLE IF EXISTS `ArchiveVersions`;
CREATE TABLE `ArchiveVersions` (
  `id` int(10) unsigned NOT NULL,
  `local_path` varchar(255) NOT NULL,
  `modified_date` datetime NOT NULL,
  `download_date` datetime NOT NULL,
  `source_domain` varchar(255) NOT NULL,
  `url` varchar(2000) NOT NULL,
  `html_title` varchar(255) NOT NULL,
  `ancestor` int(10) unsigned NOT NULL DEFAULT 0,
  `descendant` int(10) unsigned NOT NULL,
  `version` int(10) unsigned NOT NULL DEFAULT 2,
  `rss_title` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `CurrentVersions`
--

DROP TABLE IF EXISTS `CurrentVersions`;
CREATE TABLE `CurrentVersions` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `local_path` varchar(255) NOT NULL,
  `modified_date` datetime NOT NULL,
  `download_date` datetime NOT NULL,
  `source_domain` varchar(255) NOT NULL,
  `url` varchar(2000) NOT NULL,
  `html_title` varchar(255) NOT NULL,
  `ancestor` int(10) unsigned NOT NULL DEFAULT 0,
  `descendant` int(10) unsigned NOT NULL DEFAULT 0,
  `version` int(10) unsigned NOT NULL DEFAULT 1,
  `rss_title` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
