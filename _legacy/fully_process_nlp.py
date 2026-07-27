"""
Complete Integrated Analysis Pipeline
Combines all modules: aspect analysis, keywords, summarization, overall scoring
"""

import pandas as pd
import torch
from aspect_extractor import AspectSentimentAnalyzer
from keyword_extractor import KeywordExtractor
from summarizer import ReviewSummarizer
from overall_sentiment import compute_overall_score, compute_sentiment_distribution, generate_summary_metrics
import time
from datetime import datetime
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_dataset(filepath='amazon_reviews_nlp_ready-1.csv'):
    """Load and prepare the dataset"""
    print("📂 Loading dataset...")
    df = pd.read_csv(filepath)
    
    print(f"✅ Loaded {len(df):,} reviews")
    print(f"   Columns: {df.columns.tolist()}")
    
    if 'sentiment_label' in df.columns:
        print(f"\n📊 Sentiment Distribution:")
        print(df['sentiment_label'].value_counts())
    
    return df

def analyze_complete(df, sample_size=None):
    """
    Complete analysis pipeline with all modules
    
    Args:
        df: DataFrame with reviews
        sample_size: Number of reviews to analyze (None = all)
    """
    # Sample or use full dataset
    if sample_size:
        print(f"\n⚠️  Using sample of {sample_size:,} reviews for testing")
        df_analysis = df.sample(n=sample_size, random_state=42)
    else:
        print(f"\n🚀 Analyzing FULL dataset: {len(df):,} reviews")
        df_analysis = df
    
    # Extract data
    reviews = df_analysis['reviews.text'].fillna('').tolist()
    ratings = df_analysis['reviews.rating'].tolist() if 'reviews.rating' in df_analysis.columns else []
    sentiments = df_analysis['sentiment_label'].tolist() if 'sentiment_label' in df_analysis.columns else []
    
    print(f"\n{'='*70}")
    print("🔧 INITIALIZING ALL MODULES")
    print(f"{'='*70}")
    
    # Initialize all analyzers
    aspect_analyzer = AspectSentimentAnalyzer()
    keyword_extractor = KeywordExtractor()
    summarizer = ReviewSummarizer()
    
    print(f"\n{'='*70}")
    print("📊 RUNNING COMPLETE ANALYSIS")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    # 1. Aspect-based sentiment analysis
    print("\n1️⃣ Aspect Sentiment Analysis...")
    aspect_df = aspect_analyzer.analyze_aspect_sentiment(reviews)
    
    # 2. Keyword extraction
    print("\n2️⃣ Keyword Extraction...")
    top_keywords = keyword_extractor.extract_keywords(reviews, top_k=20)
    
    if sentiments:
        pros_cons = keyword_extractor.extract_pros_cons(reviews, sentiments, top_k=15)
    else:
        pros_cons = {'pros': [], 'cons': []}
    
    # 3. Summarization
    print("\n3️⃣ Generating Summary...")
    # Use first 50 reviews for quick summary
    summary_text = summarizer.summarize_reviews(reviews[:50])
    aspect_summary = summarizer.generate_aspect_summary(aspect_df)
    
    # 4. Overall scoring
    print("\n4️⃣ Computing Overall Scores...")
    if ratings:
        overall_score = compute_overall_score(ratings)
    else:
        overall_score = {}
    
    if sentiments:
        sentiment_dist = compute_sentiment_distribution(sentiments)
    else:
        sentiment_dist = {}
    
    summary_metrics = generate_summary_metrics(aspect_df)
    
    elapsed_time = time.time() - start_time
    
    # Display results
    print(f"\n{'='*70}")
    print("📊 COMPLETE ANALYSIS RESULTS")
    print(f"{'='*70}")
    
    # Aspect analysis
    print("\n🔍 ASPECT SENTIMENT BREAKDOWN:")
    print(aspect_df.to_string(index=False))
    
    # Keywords
    print(f"\n🔑 TOP KEYWORDS:")
    for word, count in top_keywords[:10]:
        print(f"  • {word}: {count}")
    
    # Pros and Cons
    if pros_cons['pros']:
        print(f"\n✅ TOP PROS (Positive Keywords):")
        for word, count in pros_cons['pros'][:10]:
            print(f"  • {word}: {count}")
    
    if pros_cons['cons']:
        print(f"\n❌ TOP CONS (Negative Keywords):")
        for word, count in pros_cons['cons'][:10]:
            print(f"  • {word}: {count}")
    
    # Summary
    print(f"\n📝 AUTO-GENERATED SUMMARY:")
    print(f"  {summary_text}")
    
    print(f"\n📋 ASPECT SUMMARY:")
    print(f"  {aspect_summary}")
    
    # Overall metrics
    print(f"\n⭐ OVERALL METRICS:")
    if overall_score:
        print(f"  Rating: {overall_score.get('out_of_5', 'N/A')} ({overall_score.get('percentage', 0)}%)")
        print(f"  Total ratings: {overall_score.get('total_count', 0):,}")
    
    if sentiment_dist:
        print(f"\n  Sentiment Distribution:")
        for sentiment, data in sentiment_dist.items():
            print(f"    {sentiment}: {data['count']:,} ({data['percentage']}%)")
    
    print(f"\n  Summary Metrics:")
    print(f"    Total mentions: {summary_metrics['total_mentions']:,}")
    print(f"    Avg positive ratio: {summary_metrics['average_positive_ratio']}%")
    print(f"    Best aspect: {summary_metrics['best_aspect']['name']} ({summary_metrics['best_aspect']['score']}%)")
    print(f"    Worst aspect: {summary_metrics['worst_aspect']['name']} ({summary_metrics['worst_aspect']['score']}%)")
    
    # Performance
    print(f"\n{'='*70}")
    print("⚡ PERFORMANCE METRICS")
    print(f"{'='*70}")
    print(f"  Total time: {elapsed_time:.2f} seconds")
    print(f"  Processing speed: {len(reviews)/elapsed_time:.0f} reviews/second")
    print(f"  Reviews analyzed: {len(reviews):,}")
    
    # Save all results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    aspect_df.to_csv(f'aspect_results_{timestamp}.csv', index=False)
    
    # Save keywords
    keyword_df = pd.DataFrame(top_keywords, columns=['keyword', 'count'])
    keyword_df.to_csv(f'keywords_{timestamp}.csv', index=False)
    
    # Save pros/cons
    if pros_cons['pros']:
        pros_df = pd.DataFrame(pros_cons['pros'], columns=['keyword', 'count'])
        pros_df.to_csv(f'pros_{timestamp}.csv', index=False)
    
    if pros_cons['cons']:
        cons_df = pd.DataFrame(pros_cons['cons'], columns=['keyword', 'count'])
        cons_df.to_csv(f'cons_{timestamp}.csv', index=False)
    
    # Save summary
    with open(f'summary_{timestamp}.txt', 'w') as f:
        f.write("REVIEW SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Auto-generated Summary:\n{summary_text}\n\n")
        f.write(f"Aspect Summary:\n{aspect_summary}\n\n")
        f.write(f"\nOverall Metrics:\n")
        if overall_score:
            f.write(f"  Rating: {overall_score.get('out_of_5', 'N/A')}\n")
        f.write(f"  Best Aspect: {summary_metrics['best_aspect']['name']}\n")
        f.write(f"  Needs Improvement: {summary_metrics['worst_aspect']['name']}\n")
    
    print(f"\n💾 ALL RESULTS SAVED:")
    print(f"  • aspect_results_{timestamp}.csv")
    print(f"  • keywords_{timestamp}.csv")
    print(f"  • pros_{timestamp}.csv")
    print(f"  • cons_{timestamp}.csv")
    print(f"  • summary_{timestamp}.txt")
    
    print(f"\n{'='*70}")
    print("✅ COMPLETE ANALYSIS FINISHED")
    print(f"{'='*70}")
    
    return {
        'aspect_df': aspect_df,
        'keywords': top_keywords,
        'pros_cons': pros_cons,
        'summary': summary_text,
        'overall_score': overall_score,
        'sentiment_dist': sentiment_dist,
        'metrics': summary_metrics
    }

# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    print("="*70)
    print("🚀 COMPLETE REVIEW ANALYSIS PIPELINE")
    print("="*70)
    
    # Load dataset
    df = load_dataset()
    
    # Choose mode
    print("\n" + "="*70)
    print("Choose analysis mode:")
    print("  1. Quick test (1000 reviews) - ~15 seconds")
    print("  2. Medium test (5,000 reviews) - ~45 seconds")
    print("  3. FULL dataset (28,332 reviews) - ~4 minutes")
    print("="*70)
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == '1':
        results = analyze_complete(df, sample_size=1000)
    elif choice == '2':
        results = analyze_complete(df, sample_size=5000)
    else:
        results = analyze_complete(df, sample_size=None)  # Full dataset


