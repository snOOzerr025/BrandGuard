import pandas as pd
from collections import Counter
import re

class KeywordExtractor:
    def __init__(self):
        pass
    
    def extract_keywords(self, reviews, top_k=20):
        words = []
        for r in reviews:
            words += clean_and_tokenize(r)
        freq = Counter(words)
        return freq.most_common(top_k)
    
    def extract_pros_cons(self, reviews, sentiments, top_k=15):
        """Extract keywords from positive and negative reviews separately"""
        positive_reviews = []
        negative_reviews = []
        
        # Separate reviews by sentiment
        for review, sentiment in zip(reviews, sentiments):
            if sentiment and str(sentiment).lower() in ['positive', 'pos', '1']:
                positive_reviews.append(review)
            elif sentiment and str(sentiment).lower() in ['negative', 'neg', '0']:
                negative_reviews.append(review)
        
        # Extract keywords for each category
        pros = self.extract_keywords(positive_reviews, top_k=top_k) if positive_reviews else []
        cons = self.extract_keywords(negative_reviews, top_k=top_k) if negative_reviews else []
        
        return {
            'pros': pros,
            'cons': cons
        }

def clean_and_tokenize(text):
    text = re.sub(r'(<.*?>)|[^a-zA-Z0-9\s]', '', text.lower())
    return [w for w in text.split() if 3 <= len(w) <= 15]
