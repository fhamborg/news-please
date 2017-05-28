import warc

from newsplease import NewsPlease

path = '/Users/felix/news/CC-NEWS-20170526201425-00088.warc'

with warc.open(path) as f:
    i = 0
    for record in f:
        html = str(record.payload.read())
        url = record.url
        article = NewsPlease.from_html(html, url)
        if article:
            print(article['title'])

        i = i + 1
        if i > 10:
            break
