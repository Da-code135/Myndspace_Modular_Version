import nltk
from textblob import TextBlob
from nltk.sentiment import SentimentIntensityAnalyzer

nltk.download('vader_lexicon')

class SentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()

    def analyze(self, text):
        blob = TextBlob(text)
        sia_score = self.sia.polarity_scores(text)
        
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity,
            'compound': sia_score['compound'],
            'sentiment': self._get_sentiment_label(sia_score['compound'])
        }

    def _get_sentiment_label(self, compound):
        if compound >= 0.05:
            return 'positive'
        elif compound <= -0.05:
            return 'negative'
        else:
            return 'neutral'
