from extractor.document import Document
from extractor.five_w_extractor import FiveWExtractor
from flask import Flask, request, jsonify
import logging


app = Flask(__name__)
log = logging.getLogger(__name__)
host = None
port = 5001
debug = False
options = None
extractor = FiveWExtractor()
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)
log.setLevel(logging.DEBUG)


def run():
    log.info("starting server on port %i", port)
    app.run(host, port, debug)
    log.info("server has stopped")


@app.route('/crawl', methods=['GET', 'POST'])
def extract():
    json_article = request.get_json()
    log.debug("retrieved raw article for extraction: %s", json_article['title'])

    document = Document(json_article['title'], json_article['description'], json_article['text'])
    extractor.parse(document)

    return jsonify(document.questions)

if __name__ == "__main__":
    run()
