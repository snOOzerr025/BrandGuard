from typing import Dict, List

import pandas as pd
import torch
from transformers import AutoTokenizer, pipeline


class ReviewAnalyzer:
    def __init__(self):
        """Initialize the sentiment analysis pipeline"""
        self.device = 0 if torch.cuda.is_available() else -1

        # Load DistilBERT for sentiment
        self.sentiment_model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=self.device,
        )

        # Load tokenizer for text preprocessing
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    def analyze_sentiment(self, reviews: List[str]) -> pd.DataFrame:
        """
        Analyze sentiment for multiple reviews
        Returns: DataFrame with review text, sentiment, and confidence score
        """
        results = []

        for review in reviews:
            # Truncate long reviews (DistilBERT max is 512 tokens)
            _ = self.tokenizer(
                review, max_length=512, truncation=True, return_tensors="pt"
            )

            # Get sentiment prediction
            sentiment = self.sentiment_model(review)[0]

            results.append(
                {
                    "review": review,
                    "sentiment": sentiment["label"],
                    "confidence": round(sentiment["score"], 3),
                }
            )

        return pd.DataFrame(results)

    def get_sentiment_distribution(self, df: pd.DataFrame) -> Dict:
        """Calculate sentiment distribution percentages"""
        total = len(df)
        positive = len(df[df["sentiment"] == "POSITIVE"])
        negative = len(df[df["sentiment"] == "NEGATIVE"])

        return {
            "positive": round((positive / total) * 100, 1),
            "negative": round((negative / total) * 100, 1),
            "total_reviews": total,
        }
