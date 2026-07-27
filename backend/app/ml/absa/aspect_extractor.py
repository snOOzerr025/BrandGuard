"""
Aspect-Based Sentiment Analysis Module
Extracts sentiment for specific product aspects: Quality, Price, Service, Delivery
Optimized for GPU acceleration with batch processing
"""

import re
from collections import defaultdict
from typing import Dict, List

import pandas as pd
import torch
from transformers import pipeline


class AspectSentimentAnalyzer:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu"):
        """
        Initialize aspect-based sentiment analyzer with GPU support

        Args:
            device: 'cuda' for GPU, 'cpu' for CPU
        """
        self.device = device
        print(f" Initializing Aspect Analyzer on {self.device.upper()}...")

        # Load DistilBERT sentiment model (fast & accurate)
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=0 if device == "cuda" else -1,
            batch_size=32,  # Process 32 reviews at once for speed
        )

        # Define aspect keywords for extraction
        self.aspect_keywords = {
            "Quality": [
                "quality",
                "good",
                "excellent",
                "great",
                "amazing",
                "perfect",
                "poor",
                "bad",
                "terrible",
                "awful",
                "defective",
                "broken",
                "sturdy",
                "durable",
                "flimsy",
                "cheap",
                "well-made",
                "poorly-made",
                "craftsmanship",
                "build",
                "material",
                "construction",
            ],
            "Price": [
                "price",
                "expensive",
                "cheap",
                "affordable",
                "value",
                "cost",
                "worth",
                "money",
                "overpriced",
                "budget",
                "deal",
                "bargain",
                "pricey",
                "costly",
                "reasonable",
                "economical",
                "pricing",
            ],
            "Service": [
                "service",
                "support",
                "help",
                "customer",
                "response",
                "staff",
                "assistance",
                "helpful",
                "unhelpful",
                "rude",
                "friendly",
                "professional",
                "representative",
                "agent",
                "team",
                "care",
                "attention",
            ],
            "Delivery": [
                "delivery",
                "shipping",
                "arrived",
                "package",
                "late",
                "fast",
                "quick",
                "slow",
                "damaged",
                "box",
                "courier",
                "dispatch",
                "tracking",
                "packaging",
                "ship",
                "received",
                "delivered",
            ],
        }

        print(" Aspect Analyzer ready!")

    def extract_aspect_mentions(self, reviews: List[str]) -> Dict[str, List[tuple]]:
        """
        Extract which aspects are mentioned in which reviews

        Args:
            reviews: List of review texts

        Returns:
            Dictionary mapping aspects to list of (review_index, sentence) tuples
        """
        aspect_mentions = defaultdict(list)

        for idx, review in enumerate(reviews):
            # Split into sentences for better context
            sentences = re.split(r"[.!?]+", review)

            for aspect, keywords in self.aspect_keywords.items():
                for sentence in sentences:
                    sentence_lower = sentence.lower().strip()
                    if not sentence_lower:
                        continue

                    # Check if any keyword appears in this sentence
                    if any(keyword in sentence_lower for keyword in keywords):
                        aspect_mentions[aspect].append((idx, sentence.strip()))
                        break  # Only count once per aspect per review

        return aspect_mentions

    def analyze_aspect_sentiment(self, reviews: List[str]) -> pd.DataFrame:
        """
        Analyze sentiment for each aspect across all reviews

        Args:
            reviews: List of review texts

        Returns:
            DataFrame with aspect-level sentiment statistics
        """
        print(f"Analyzing aspects in {len(reviews)} reviews...")

        # Extract aspect mentions
        aspect_mentions = self.extract_aspect_mentions(reviews)

        # Analyze sentiment for each aspect
        aspect_results = []

        for aspect, mentions in aspect_mentions.items():
            if not mentions:
                # No mentions of this aspect
                aspect_results.append(
                    {
                        "aspect": aspect,
                        "mention_count": 0,
                        "positive_count": 0,
                        "negative_count": 0,
                        "positive_ratio": 0.0,
                        "sentiment_score": 0.0,
                    }
                )
                continue

            try:
                # Extract sentences mentioning this aspect
                sentences = [
                    sentence
                    for _, sentence in mentions
                    if sentence and sentence.strip()
                ]

                if not sentences:
                    # No valid sentences
                    aspect_results.append(
                        {
                            "aspect": aspect,
                            "mention_count": len(mentions),
                            "positive_count": 0,
                            "negative_count": 0,
                            "positive_ratio": 0.0,
                            "sentiment_score": 0.0,
                        }
                    )
                    continue

                # Batch sentiment analysis (GPU accelerated)
                sentiments = self.sentiment_pipeline(sentences)

                # Count positive/negative
                positive_count = sum(1 for s in sentiments if s["label"] == "POSITIVE")
                negative_count = len(sentiments) - positive_count

                # Calculate metrics
                if len(sentiments) > 0:
                    positive_ratio = (positive_count / len(sentiments)) * 100
                    # Sentiment score: +1 for positive, -1 for negative,
                    # weighted by confidence
                    sentiment_score = sum(
                        s["score"] if s["label"] == "POSITIVE" else -s["score"]
                        for s in sentiments
                    ) / len(sentiments)
                else:
                    positive_ratio = 0.0
                    sentiment_score = 0.0
            except Exception as e:
                # If sentiment analysis fails for this aspect, use default values
                print(f"Warning: Sentiment analysis failed for aspect '{aspect}': {e}")
                positive_count = 0
                negative_count = 0
                positive_ratio = 0.0
                sentiment_score = 0.0

            aspect_results.append(
                {
                    "aspect": aspect,
                    "mention_count": len(mentions),
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "positive_ratio": round(positive_ratio, 1),
                    "sentiment_score": round(sentiment_score, 3),
                }
            )

        # Create DataFrame
        if not aspect_results:
            # Return empty DataFrame with expected columns if no results
            df = pd.DataFrame(
                columns=[
                    "aspect",
                    "mention_count",
                    "positive_count",
                    "negative_count",
                    "positive_ratio",
                    "sentiment_score",
                ]
            )
        else:
            df = pd.DataFrame(aspect_results)

            # Sort by mention count (most discussed aspects first)
            # Only sort if DataFrame is not empty and has the column
            if not df.empty and "mention_count" in df.columns:
                df = df.sort_values("mention_count", ascending=False).reset_index(
                    drop=True
                )

        print("✅ Aspect analysis complete!")
        return df

    def get_aspect_examples(
        self,
        reviews: List[str],
        aspect: str,
        sentiment: str = "negative",
        limit: int = 5,
    ) -> List[str]:
        """
        Get example reviews mentioning a specific aspect with given sentiment

        Args:
            reviews: List of review texts
            aspect: Aspect name ('Quality', 'Price', 'Service', 'Delivery')
            sentiment: 'positive' or 'negative'
            limit: Maximum number of examples to return

        Returns:
            List of example sentences
        """
        aspect_mentions = self.extract_aspect_mentions(reviews)

        if aspect not in aspect_mentions:
            return []

        sentences = [sentence for _, sentence in aspect_mentions[aspect]]

        # Analyze sentiment
        sentiments = self.sentiment_pipeline(sentences)

        # Filter by sentiment
        examples = []
        for sentence, sent_result in zip(sentences, sentiments):
            if sent_result["label"].lower() == sentiment.upper():
                examples.append(sentence)
                if len(examples) >= limit:
                    break

        return examples

    def generate_aspect_report(self, reviews: List[str]) -> Dict:
        """
        Generate comprehensive aspect analysis report

        Args:
            reviews: List of review texts

        Returns:
            Dictionary with full aspect analysis and examples
        """
        print("\n📊 Generating Aspect Report...")

        # Get aspect sentiment analysis
        aspect_df = self.analyze_aspect_sentiment(reviews)

        # Generate report
        report = {"summary": aspect_df.to_dict("records"), "details": {}}

        # Add examples for each aspect
        for _, row in aspect_df.iterrows():
            aspect = row["aspect"]

            if row["mention_count"] > 0:
                report["details"][aspect] = {
                    "positive_examples": self.get_aspect_examples(
                        reviews, aspect, "positive", limit=3
                    ),
                    "negative_examples": self.get_aspect_examples(
                        reviews, aspect, "negative", limit=3
                    ),
                }

        print("✅ Report generated!")
        return report


# ========== USAGE EXAMPLE ==========

if __name__ == "__main__":
    # Sample reviews for testing
    sample_reviews = [
        "Great product! The quality is amazing and delivery was super fast.",
        "Terrible experience. Product broke within a week. Very poor quality.",
        "Good value for money but customer service could be better.",
        "Excellent quality but a bit expensive for what you get.",
        "Fast shipping and great packaging! Love the build quality.",
        "Product doesn't match description. Very disappointed with the quality.",
        "Decent product for the price. Service was helpful.",
        "Outstanding quality! Exactly what I needed. Worth every penny.",
        "Poor quality materials used. Broke after 2 days.",
        "Great customer support team! They helped me quickly.",
        "Overpriced for the quality. Expected better.",
        "Delivery was late but product quality is good.",
        "Excellent value. Quality exceeds expectations for this price.",
        "Service was rude and unhelpful. Product is okay though.",
        "Amazing quality and fast delivery. Highly recommend!",
    ]

    # Initialize analyzer
    analyzer = AspectSentimentAnalyzer()

    # Analyze aspects
    print("\n" + "=" * 60)
    aspect_results_df = analyzer.analyze_aspect_sentiment(sample_reviews)
    print("\n📊 ASPECT SENTIMENT ANALYSIS RESULTS:\n")
    print(aspect_results_df.to_string(index=False))

    # Generate full report
    print("\n" + "=" * 60)
    report = analyzer.generate_aspect_report(sample_reviews)

    # Display examples for negative aspects
    print("\n🔴 NEGATIVE ASPECT EXAMPLES:\n")
    for aspect, details in report["details"].items():
        if details["negative_examples"]:
            print(f"\n{aspect}:")
            for example in details["negative_examples"]:
                print(f"  • {example}")

    print("\n" + "=" * 60)
    print("✅ Aspect analysis complete! Ready for integration.")
