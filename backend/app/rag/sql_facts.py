"""
rag/sql_facts.py — Parameterized Deterministic SQL Fact Aggregator
------------------------------------------------------------------
Computes exact review counts, Net Sentiment (Chattermill formula), and
Leave-One-Out counterfactual Star Impact directly in database queries.
Injected as immutable <deterministic_sql_facts> XML block into prompt.
"""
import uuid
from typing import Any, Dict, List, Optional
from sqlmodel import Session, func, select

from backend.app.models.domain import PolarityLabel, Product, Review, SentimentResult


class SQLFactsAggregator:
    """
    Computes deterministic quantitative metrics without LLM estimation.
    """

    @staticmethod
    def compute_facts(
        product_id: uuid.UUID,
        user_id: uuid.UUID,
        session: Session,
        aspect_focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates exact SQL metrics:
          - total_reviews
          - average_star_rating
          - aspect_metrics: Dict[aspect -> {mentions, positive, neutral, negative, net_sentiment, star_impact}]
        """
        # Global product reviews
        reviews = session.exec(
            select(Review).where(Review.product_id == product_id, Review.user_id == user_id)
        ).all()

        total_count = len(reviews)
        if total_count == 0:
            return {
                "total_reviews": 0,
                "average_rating": 0.0,
                "aspects": {},
                "xml_block": "<deterministic_sql_facts>\nNo review records found.\n</deterministic_sql_facts>",
            }

        all_ratings = [r.rating for r in reviews]
        sum_ratings = sum(all_ratings)
        avg_rating = sum_ratings / total_count

        # Pull SentimentResult rows
        sentiments = session.exec(
            select(SentimentResult).where(
                SentimentResult.product_id == product_id,
                SentimentResult.user_id == user_id,
            )
        ).all()

        # Group sentiments by aspect
        by_aspect: Dict[str, List[SentimentResult]] = {}
        for s in sentiments:
            by_aspect.setdefault(s.aspect_category, []).append(s)

        aspect_metrics: Dict[str, Dict[str, Any]] = {}

        for asp, s_list in by_aspect.items():
            if aspect_focus and asp.lower() != aspect_focus.lower():
                continue

            pos = sum(1 for s in s_list if s.polarity == PolarityLabel.POSITIVE)
            neu = sum(1 for s in s_list if s.polarity == PolarityLabel.NEUTRAL)
            neg = sum(1 for s in s_list if s.polarity == PolarityLabel.NEGATIVE)
            mentions = len(s_list)

            # Chattermill Net Sentiment: ((P - N) / (P + Neu + N)) * 100
            net_sentiment = ((pos - neg) / max(mentions, 1)) * 100.0

            # Thematic Leave-One-Out Star Impact:
            # Reviews mentioning this aspect
            asp_rev_ids = {s.review_id for s in s_list}
            excl_ratings = [r.rating for r in reviews if r.id not in asp_rev_ids]
            if excl_ratings:
                mean_excl = sum(excl_ratings) / len(excl_ratings)
                star_impact = avg_rating - mean_excl
            else:
                star_impact = 0.0

            aspect_metrics[asp] = {
                "mentions": mentions,
                "positive": pos,
                "neutral": neu,
                "negative": neg,
                "net_sentiment": round(net_sentiment, 2),
                "star_impact": round(star_impact, 4),
            }

        # Format XML block
        xml_lines = ["<deterministic_sql_facts>"]
        xml_lines.append(f"  <total_reviews>{total_count}</total_reviews>")
        xml_lines.append(f"  <product_average_rating>{avg_rating:.2f}</product_average_rating>")

        for asp, m in aspect_metrics.items():
            xml_lines.append(f"  <aspect name=\"{asp}\">")
            xml_lines.append(f"    <mentions>{m['mentions']}</mentions>")
            xml_lines.append(f"    <net_sentiment>{m['net_sentiment']:+.1f}</net_sentiment>")
            xml_lines.append(f"    <star_impact>{m['star_impact']:+.2f}★</star_impact>")
            xml_lines.append(f"    <breakdown positive=\"{m['positive']}\" neutral=\"{m['neutral']}\" negative=\"{m['negative']}\" />")
            xml_lines.append(f"  </aspect>")

        xml_lines.append("</deterministic_sql_facts>")

        return {
            "total_reviews": total_count,
            "average_rating": round(avg_rating, 2),
            "aspects": aspect_metrics,
            "xml_block": "\n".join(xml_lines),
        }
