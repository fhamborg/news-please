from setuptools import setup, find_packages
from distutils.command.install import INSTALL_SCHEMES
import sys, os


setup(name='news-please',
      version='1.1.15',
      description="news-please is an open source easy-to-use news extractor that just works.",
      long_description="""\
news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website.""",
      classifiers=[
	'Development Status :: 4 - Beta',
	'Environment :: Console',
	'Intended Audience :: Developers',
	'Intended Audience :: Science/Research',
	'License :: OSI Approved :: Apache Software License',
	'Operating System :: MacOS',
	'Operating System :: Microsoft',
	'Operating System :: POSIX :: Linux',
	'Programming Language :: Python :: 2.7',
	'Programming Language :: Python :: 3.0',
	'Programming Language :: Python :: 3.1',
	'Programming Language :: Python :: 3.2',
	'Programming Language :: Python :: 3.3',
	'Programming Language :: Python :: 3.4',
	'Programming Language :: Python :: 3.5',
	'Programming Language :: Python :: 3.6',
	'Topic :: Internet',
	'Topic :: Scientific/Engineering :: Information Analysis',
      ],
      keywords='news crawler,news scraper,news extractor,crawler,extractor,scraper,information retrieval',
      author='Felix Hamborg',
      author_email='felix.hamborg@uni-konstanz.de',
      url='https://github.com/fhamborg/news-please',
      download_url='https://github.com/fhamborg/news-please',
      license='Apache License 2.0',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'Scrapy>=1.1.0',
	'PyMySQL>=0.7.9',
	'hjson>=1.5.8',
	'elasticsearch>=2.4',
	'beautifulsoup4>=4.5.1',
	'readability-lxml>=0.6.2',
	'langdetect>=1.0.7',
	'python-dateutil>=2.4.0',
	'plac>=0.9.6'
      ],
      extras_require={
	':python_version == "2.7"':[
		'newspaper',
	],
	':python_version >= "3.0"':[
		'newspaper3k',
	],
      },
      entry_points={
      	'console_scripts': ['news-please = newsplease.__main__:main',],
	},
      )
