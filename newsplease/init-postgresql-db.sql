--
-- Table structure for table ArchiveVersions
--

DROP TABLE IF EXISTS ArchiveVersions;
CREATE TABLE ArchiveVersions (
  id SERIAL PRIMARY KEY,
  date_modify timestamp(0) NOT NULL,
  date_download timestamp(0) NOT NULL,
  localpath varchar(255) NOT NULL,
  filename varchar(2000) NOT NULL,
  source_domain varchar(255) NOT NULL,
  url varchar(2000) NOT NULL,
  image_url varchar(2000),
  title varchar(255) NOT NULL,
  title_page varchar(255) NOT NULL,
  title_rss varchar(255),
  maintext text NOT NULL,
  description text,
  date_publish timestamp(0),
  authors varchar(255) ARRAY,
  language varchar(255),
  ancestor int NOT NULL DEFAULT 0,
  descendant int NOT NULL,
  version int NOT NULL DEFAULT 2
);

--
-- Table structure for table CurrentVersions
--

DROP TABLE IF EXISTS CurrentVersions;
CREATE TABLE CurrentVersions (
  id SERIAL PRIMARY KEY,
  date_modify timestamp(0) NOT NULL,
  date_download timestamp(0) NOT NULL,
  localpath varchar(255) NOT NULL,
  filename varchar(2000) NOT NULL,
  source_domain varchar(255) NOT NULL,
  url varchar(2000) NOT NULL,
  image_url varchar(2000),
  title varchar(255) NOT NULL,
  title_page varchar(255) NOT NULL,
  title_rss varchar(255),
  maintext text NOT NULL,
  description text,
  date_publish timestamp(0),
  authors varchar(255) ARRAY,
  language varchar(255),
  ancestor int NOT NULL DEFAULT 0,
  descendant int NOT NULL DEFAULT 0,
  version int NOT NULL DEFAULT 1
);
