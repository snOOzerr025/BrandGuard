import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Product Review Hub",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .review-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .product-name {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .review-text {
        font-size: 1rem;
        color: #333;
        line-height: 1.6;
        margin: 1rem 0;
    }
    .review-meta {
        font-size: 0.9rem;
        color: #666;
        font-style: italic;
    }
    .rating-stars {
        font-size: 1.5rem;
        color: #ffa500;
    }
    </style>
""", unsafe_allow_html=True)

# Data storage file
DATA_FILE = "reviews.json"

def load_reviews():
    """Load reviews from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_reviews(reviews):
    """Save reviews to JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)

def get_star_rating(rating):
    """Convert numeric rating to star emoji"""
    return "⭐" * int(rating)

def main():
    # Header
    st.markdown('<h1 class="main-header">⭐ Product Review Hub ⭐</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choose a page", ["📝 Submit Review", "📖 View Reviews", "📊 Statistics"])
    
    # Load existing reviews
    reviews = load_reviews()
    
    if page == "📝 Submit Review":
        st.header("Share Your Product Review")
        st.markdown("Help others make informed decisions by sharing your experience!")
        
        with st.form("review_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                product_name = st.text_input("Product Name *", placeholder="e.g., iPhone 15 Pro")
                reviewer_name = st.text_input("Your Name *", placeholder="e.g., John Doe")
            
            with col2:
                rating = st.slider("Rating *", min_value=1, max_value=5, value=5, help="Rate from 1 to 5 stars")
                category = st.selectbox("Category", ["Electronics", "Clothing", "Food & Beverages", "Books", "Home & Garden", "Sports", "Beauty", "Other"])
            
            review_text = st.text_area("Your Review *", placeholder="Share your detailed experience with this product...", height=150)
            
            # Additional fields
            col3, col4 = st.columns(2)
            with col3:
                price_paid = st.number_input("Price Paid (Optional)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            with col4:
                recommend = st.radio("Would you recommend?", ["Yes", "No", "Maybe"], horizontal=True)
            
            submitted = st.form_submit_button("Submit Review", use_container_width=True)
            
            if submitted:
                if product_name and reviewer_name and review_text:
                    new_review = {
                        "id": len(reviews) + 1,
                        "product_name": product_name,
                        "reviewer_name": reviewer_name,
                        "rating": rating,
                        "review_text": review_text,
                        "category": category,
                        "price_paid": price_paid if price_paid > 0 else None,
                        "recommend": recommend,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    reviews.append(new_review)
                    save_reviews(reviews)
                    
                    st.success("✅ Your review has been submitted successfully! Thank you for sharing.")
                    st.balloons()
                else:
                    st.error("⚠️ Please fill in all required fields (marked with *)")
    
    elif page == "📖 View Reviews":
        st.header("Browse Product Reviews")
        
        if not reviews:
            st.info("📭 No reviews yet. Be the first to share a review!")
        else:
            # Filters
            st.subheader("Filters")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_category = st.selectbox("Filter by Category", ["All"] + list(set([r["category"] for r in reviews])))
            with col2:
                filter_rating = st.selectbox("Filter by Rating", ["All", "5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"])
            with col3:
                sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Highest Rating", "Lowest Rating"])
            
            # Apply filters
            filtered_reviews = reviews.copy()
            
            if filter_category != "All":
                filtered_reviews = [r for r in filtered_reviews if r["category"] == filter_category]
            
            if filter_rating != "All":
                rating_value = int(filter_rating.split()[0])
                filtered_reviews = [r for r in filtered_reviews if r["rating"] == rating_value]
            
            # Apply sorting
            if sort_by == "Newest First":
                filtered_reviews.sort(key=lambda x: x["timestamp"], reverse=True)
            elif sort_by == "Oldest First":
                filtered_reviews.sort(key=lambda x: x["timestamp"])
            elif sort_by == "Highest Rating":
                filtered_reviews.sort(key=lambda x: x["rating"], reverse=True)
            elif sort_by == "Lowest Rating":
                filtered_reviews.sort(key=lambda x: x["rating"])
            
            st.markdown(f"**Showing {len(filtered_reviews)} review(s)**")
            st.markdown("---")
            
            # Display reviews
            for review in filtered_reviews:
                with st.container():
                    st.markdown(f"""
                        <div class="review-card">
                            <div class="product-name">{review['product_name']}</div>
                            <div class="rating-stars">{get_star_rating(review['rating'])}</div>
                            <div class="review-text">{review['review_text']}</div>
                            <div class="review-meta">
                                Reviewed by <strong>{review['reviewer_name']}</strong> | 
                                Category: {review['category']} | 
                                {review['timestamp']}
                            </div>
                    """, unsafe_allow_html=True)
                    
                    # Additional info
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        if review.get('price_paid'):
                            st.caption(f"💰 Price Paid: ${review['price_paid']:.2f}")
                    with col_info2:
                        recommend_emoji = "✅" if review['recommend'] == "Yes" else "❌" if review['recommend'] == "No" else "🤷"
                        st.caption(f"{recommend_emoji} Recommendation: {review['recommend']}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("---")
    
    elif page == "📊 Statistics":
        st.header("Review Statistics")
        
        if not reviews:
            st.info("📭 No reviews yet. Statistics will appear once reviews are submitted.")
        else:
            total_reviews = len(reviews)
            avg_rating = sum(r["rating"] for r in reviews) / total_reviews
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Reviews", total_reviews)
            with col2:
                st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
            with col3:
                categories = [r["category"] for r in reviews]
                most_common_category = max(set(categories), key=categories.count)
                st.metric("Most Reviewed Category", most_common_category)
            with col4:
                recommendations = [r["recommend"] for r in reviews]
                yes_count = recommendations.count("Yes")
                recommend_percentage = (yes_count / total_reviews) * 100
                st.metric("Recommendation Rate", f"{recommend_percentage:.1f}%")
            
            st.markdown("---")
            
            # Rating distribution
            st.subheader("Rating Distribution")
            rating_counts = {}
            for i in range(1, 6):
                rating_counts[i] = sum(1 for r in reviews if r["rating"] == i)
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.bar_chart(rating_counts)
            
            with col_chart2:
                category_counts = {}
                for review in reviews:
                    cat = review["category"]
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                st.bar_chart(category_counts)
            
            # Recent reviews preview
            st.subheader("Recent Reviews")
            recent_reviews = sorted(reviews, key=lambda x: x["timestamp"], reverse=True)[:5]
            for review in recent_reviews:
                st.markdown(f"**{review['product_name']}** - {get_star_rating(review['rating'])} by {review['reviewer_name']} ({review['timestamp']})")

if __name__ == "__main__":
    main()

