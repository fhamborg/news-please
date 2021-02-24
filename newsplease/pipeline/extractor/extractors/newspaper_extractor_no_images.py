from .newspaper_extractor import NewspaperExtractor


class NewspaperExtractorNoImages(NewspaperExtractor):
    def _article_kwargs(self):
        return {"fetch_images": False}
