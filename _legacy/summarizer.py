from transformers import pipeline
import torch

class ReviewSummarizer:
    def __init__(self, device=None):
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        self.summarizer = pipeline(
            "summarization", 
            model="facebook/bart-large-cnn", 
            device=0 if device == 'cuda' else -1
        )
    
    def summarize(self, big_text, min_length=30, max_length=90):
        return self.summarizer(big_text, min_length=min_length, max_length=max_length, do_sample=False)[0]['summary_text']
    
    def summarize_reviews(self, reviews, min_length=50, max_length=150):
        """Summarize a list of reviews by joining them"""
        if not reviews:
            return "No reviews to summarize."
        # Join reviews with spaces
        combined_text = " ".join(reviews)
        # Truncate if too long (BART has token limits)
        max_chars = 1024 * 4  # Approximate token limit
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars]
        return self.summarize(combined_text, min_length=min_length, max_length=max_length)
    
    def generate_aspect_summary(self, aspect_df):
        """Generate a text summary from aspect analysis DataFrame"""
        if aspect_df.empty:
            return "No aspect data available."
        
        summary_parts = []
        for _, row in aspect_df.iterrows():
            aspect = row.get('aspect', 'Unknown')
            mention_count = row.get('mention_count', 0)
            positive_ratio = row.get('positive_ratio', 0)
            
            if mention_count > 0:
                summary_parts.append(
                    f"{aspect}: {mention_count} mentions, {positive_ratio}% positive sentiment"
                )
        
        if summary_parts:
            return "; ".join(summary_parts)
        return "No aspect mentions found."
