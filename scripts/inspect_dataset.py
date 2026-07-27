"""Quick inspection of the existing Amazon reviews dataset."""
import os
import pandas as pd

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "amazon_reviews_nlp_ready-1.csv")

df = pd.read_csv(CSV_PATH)
print(f"Total rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(f"Unique products: {df[' name'].nunique()}")
print(f"\nSentiment distribution:")
print(df["sentiment_label"].value_counts())
print(f"\nRating distribution:")
print(df["reviews.rating"].value_counts().sort_index())
print(f"\nSample reviews:")
print(df[["reviews.text", "reviews.rating", "sentiment_label"]].head(3).to_string())
