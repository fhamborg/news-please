from src.Cleaner import *
from src.Extractor import *
from src.IO_handler.InputHandler import *
from src.IO_handler.ArgumentHandler import *
from src.comparer.Comparer import *
from src.help_classes.Article import *
import time


"""This is the mainclass of this program, which connects all the modules"""


class KM4ArticleExtractor():

    def __init__(self):
        self.input_handler = InputHandler()
        self.extractor = Extractor()
        self.cleaner = Cleaner()
        self.comparer = Comparer()
        self.output_handler = Outputhandler()
        self.argument_handler = ArgumentHandler()

    def extract_and_upload(self, article_list):
        """Connects most of the parts
        Takes an list of ArticleRaws and runs each through the extractor
        after that it uploads the article and sets the latest id in the databasehandler.
        Every 20 articles it saves the latest extracted ID"""
        counter = 0
        for article_raw in article_list:
            article = Article()
            article.merge_with_articleraw(article_raw)
            list_article_candidate = self.extractor.extract(article_raw)
            list_article_candidate = self.cleaner.clean(list_article_candidate)
            article = self.comparer.compare(list_article_candidate, article)
            self.output_handler.upload(article)
            counter += 1
            if counter <= 20:
                self.input_handler.set_last_id()
                counter = 0
            print(article.id)
            #es = Elasticsearch()
            #article_doc = es.get(index="topic", doc_type='article', id=article.id)
            #print(article_doc['_source'])
        self.input_handler.set_last_id()

    def main(self):
        """Connects the methods and creates an endless mode if endless_mode in the config.ini is True"""
        if self.argument_handler.argument_cleanup():
            print("Cleaned Database")
        else:
            article_list = self.input_handler.download_from_db()
            self.extract_and_upload(article_list)
            if self.input_handler.config_handler.endless_mode:
                while True:
                    time.sleep(self.input_handler.config_handler.sleep_intervall)
                    new_articles_raws = self.input_handler.download_from_db()
                    if new_articles_raws:
                        print('new articles found')
                        self.extract_and_upload(new_articles_raws)
                    else:
                        print('no new articles found')



if __name__ == "__main__":
    km4 = KM4ArticleExtractor()
    km4.main()
