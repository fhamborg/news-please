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
    entry_points={
        "console_scripts": [
            "news-please = newsplease.__main__:main",
            "news-please-cc = newsplease.examples.commoncrawl:main",
        ]
    },
)
