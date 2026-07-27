"""
Full Dataset Processing Pipeline
Analyzes 28,332 Amazon product reviews with GPU acceleration
"""

import pandas as pd
import torch
from aspect_extractor import AspectSentimentAnalyzer
import time
from datetime import datetime


def load_dataset (filepath=r'D:\code\E_Hack_Project\amazon_reviews.csv'):


    print(" Loading dataset...")
    df = pd.read_csv(filepath)

    print(f" Loaded {len(df):,} reviews")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"\n Sentiment Distribution:")
    print(df['sentiment_label'].value_counts())

    return df


def analyze_full_dataset(df, sample_size=None):
    """
    Analyze all reviews or a sample

    Args:
        df: DataFrame with reviews
        sample_size: If set, analyze only this many reviews (for testing)
    """
    # Use sample or full dataset
    if sample_size:
        print(f"\n⚠  Using sample of {sample_size:,} reviews for testing")
        df_analysis = df.sample(n=sample_size, random_state=42)
    else:
        print(f"\n Analyzing FULL dataset: {len(df):,} reviews")
        df_analysis = df

    # Extract review texts
    reviews = df_analysis['reviews.text'].tolist()

    # Initialize analyzer with GPU
    print("\n🔧 Initializing GPU-accelerated analyzer...")
    analyzer = AspectSentimentAnalyzer(device='cuda' if torch.cuda.is_available() else 'cpu')

    # Run analysis with timing
    print(f"\n⏱️  Starting analysis at {datetime.now().strftime('%H:%M:%S')}...")
    start_time = time.time()

    # Analyze aspects
    aspect_df = analyzer.analyze_aspect_sentiment(reviews)

    # Generate full report with examples
    report = analyzer.generate_aspect_report(reviews)

    elapsed_time = time.time() - start_time

    # Display results
    print("\n" + "=" * 70)
    print("📊 ASPECT SENTIMENT ANALYSIS RESULTS")
    print("=" * 70)
    print(aspect_df.to_string(index=False))

    print("\n" + "=" * 70)
    print("🔴 TOP NEGATIVE ASPECT EXAMPLES")
    print("=" * 70)
    for aspect, details in report['details'].items():
        if details['negative_examples']:
            print(f"\n{aspect}:")
            for i, example in enumerate(details['negative_examples'][:3], 1):
                print(f"  {i}. {example[:100]}...")  # First 100 chars

    print("\n" + "=" * 70)
    print(" ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"⏱  Total processing time: {elapsed_time:.2f} seconds")
    print(f" Speed: {len(reviews) / elapsed_time:.0f} reviews/second")
    print(f" Results ready for export and visualization")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'aspect_analysis_results_{timestamp}.csv'
    aspect_df.to_csv(output_file, index=False)
    print(f"\n Saved results to: {output_file}")

    return aspect_df, report


def compare_with_ground_truth(df, aspect_df):
    """Compare your aspect analysis with provided sentiment labels"""
    print("\n" + "=" * 70)
    print("🎯 MODEL VALIDATION")
    print("=" * 70)

    # Count ground truth distribution
    gt_counts = df['sentiment_label'].value_counts()
    total = len(df)

    print("Ground Truth Distribution:")
    for label, count in gt_counts.items():
        print(f"  {label}: {count:,} ({count / total * 100:.1f}%)")

    print("\nYour Aspect Analysis Shows:")
    print(aspect_df.to_string(index=False))


# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 AMAZON REVIEWS - FULL DATASET ANALYSIS")
    print("=" * 70)

    # Load dataset
    df = load_dataset('amazon_reviews_nlp_ready-1.csv')

    # Ask user: sample or full?
    print("\n" + "=" * 70)
    print("Choose analysis mode:")
    print("  1. Quick test (1,000 reviews) - ~5 seconds")
    print("  2. Medium test (5,000 reviews) - ~15 seconds")
    print("  3. FULL dataset (28,332 reviews) - ~35 seconds")
    print("=" * 70)

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        aspect_df, report = analyze_full_dataset(df, sample_size=1000)
    elif choice == '2':
        aspect_df, report = analyze_full_dataset(df, sample_size=5000)
    else:
        aspect_df, report = analyze_full_dataset(df, sample_size=None)  # Full dataset

    # Compare with ground truth
    compare_with_ground_truth(df, aspect_df)

    print("\n" + "=" * 70)
    print("=" * 70)
