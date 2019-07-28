from setuptools import setup, find_packages

setup(
    name="news-please",
    version="1.4.21",
    description="news-please is an open source easy-to-use news extractor that just works.",
    long_description="""\
news-please is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website. Furthermore, its API allows developers to access the exctraction functionality within their software. news-please also implements a workflow optimized for the news archive provided by commoncrawl.org, allowing users to efficiently crawl and extract news articles including various filter options.""",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    keywords="news crawler news scraper news extractor crawler extractor scraper information retrieval",
    author="Felix Hamborg",
    author_email="felix.hamborg@uni-konstanz.de",
    url="https://github.com/fhamborg/news-please",
    download_url="https://github.com/fhamborg/news-please",
    license="Apache License 2.0",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
        if not line.startswith("#")
    ],
    extras_require={
        ':python_version == "2.7"': [
            "newspaper",
            "future>=0.16.0",
            "hurry.filesize>=0.9",
        ],
        ':python_version >= "3.0"': ["newspaper3k"],
        ':sys_platform == "win32"': ["pywin32>=220"],
    },
    entry_points={
        "console_scripts": [
            "news-please = newsplease.__main__:main",
            "news-please-cc = newsplease.examples.commoncrawl:main",
        ]
    },
)
