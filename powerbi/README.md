# 📊 BrandGuard Power BI Analytics & MIS Dashboard Guide

This directory contains the operational data pipelines and specification for the **BrandGuard Power BI Reporting Metrics System**, tailored for the **Axis Bank Business Solutions Group (BSG)** internship workflow.

---

## 🗂️ 1. Data Model & Architecture

The reporting system consumes clean, relational CSV datasets exported by [`scripts/export_bi_dataset.py`](../scripts/export_bi_dataset.py) into `powerbi/data/`:

| File | Type | Description | Primary Key / Foreign Keys |
|:---|:---:|:---|:---|
| `products.csv` | **Dimension** | Tracked products/apps, brand health scores, and net sentiment | `product_id` (PK) |
| `reviews.csv` | **Fact** | Customer review records, ratings (1–5), verified flags, and rating discrepancies | `review_id` (PK), `product_id` (FK) |
| `sentiment_results.csv` | **Fact** | Aspect-based sentiment analysis (ABSA) outputs with polarity scores | `sentiment_id` (PK), `review_id` (FK), `product_id` (FK) |
| `alerts.csv` | **Fact** | Statistical $3\sigma$ breaches and anomalies, **left-joined with JIRA tickets** | `alert_id` (PK), `product_id` (FK), `jira_key` |

### Recommended Power BI Data Model (Model View)
In Power BI Desktop, navigate to the **Model View** and verify the following $1 : \text{Many}$ relationships (Single Cross-Filter Direction):

```
       [products]
       ├── (1 : ∞) ──> [reviews]
       │                  └── (1 : ∞) ──> [sentiment_results]
       └── (1 : ∞) ──> [alerts] (includes JIRA ticket fields)
```

1. `products[product_id]` $\rightarrow$ `reviews[product_id]` ($1 : \text{Many}$)
2. `reviews[review_id]` $\rightarrow$ `sentiment_results[review_id]` ($1 : \text{Many}$)
3. `products[product_id]` $\rightarrow$ `alerts[product_id]` ($1 : \text{Many}$)

---

## 🖥️ 2. Dashboard Pages Specification

### Page 1: Customer Sentiment & Aspect Health Overview
*Executive view answering: Which product dimensions drive customer delight or churn?*

#### Key Performance Indicators (Cards along top ribbon):
1. **Net Sentiment Score (NSS)**: Formatted as percentage (Measure: `[Net Sentiment Score]`).
2. **Total Review Volume**: Formatted as integer (Measure: `[Total Reviews]`).
3. **Average Star Rating**: Formatted as decimal (e.g. `4.2 ★`).
4. **Silent Churn (Rating Discrepancies)**: Percentage of reviews with $\ge 4$ stars but negative text sentiment (Measure: `[Discrepancy Rate]`).

#### Main Visuals:
- **Aspect Sentiment Matrix (Stacked Horizontal Bar Chart)**:
  - **Y-Axis**: `sentiment_results[aspect_category]`
  - **X-Axis**: Count of sentiments
  - **Legend**: `sentiment_results[polarity]` (Color code: Green = Positive, Gray = Neutral, Red = Negative)
- **Review Volume & Sentiment Timeline (Line Chart)**:
  - **X-Axis**: `reviews[reviewed_at]` (Date Hierarchy: Day / Week)
  - **Y-Axis**: Count of reviews and Average Rating
- **Product Slicer (Dropdown / Tiles)**:
  - Field: `products[name]`

---

### Page 2: Statistical Breaches & JIRA Operations (MIS Dashboard)
*Operational management view matching the JD's "MIS dashboards on JIRA" and process tracking.*

#### Key Performance Indicators (Top Cards):
1. **Total Anomalies Detected**: Count of rows in `alerts` (Measure: `[Total Alerts]`).
2. **Critical $3\sigma$ Breaches**: Count of `CRITICAL` severity incidents (Measure: `[Critical Alerts]`).
3. **Open JIRA Tickets**: Tickets in `To Do` or `In Progress` status (Measure: `[Open JIRA Tickets]`).
4. **Incident Resolution Rate**: Percentage of ticketed alerts marked `Done` (Measure: `[JIRA Resolution Rate]`).

#### Main Visuals:
- **Breaches by Severity & Aspect (Clustered Column Chart)**:
  - **X-Axis**: `alerts[aspect_category]`
  - **Y-Axis**: Count of `alert_id`
  - **Legend**: `alerts[severity]` (`CRITICAL`, `HIGH`, `MEDIUM`)
- **JIRA Incident Status Breakdown (Donut Chart)**:
  - **Legend**: `alerts[jira_status]` (`To Do`, `In Progress`, `Done`, `Unassigned`)
  - **Values**: Count of `alert_id`
- **Active Incident Telemetry Table (Grid)**:
  - **Columns**:
    - `alerts[created_at]` (Timestamp)
    - `alerts[aspect_category]` (Aspect)
    - `alerts[severity]` (Severity)
    - `alerts[z_score]` (EWMA deviation score)
    - `alerts[star_impact]` (Leave-One-Out star drag, e.g. $-0.42\star$)
    - `alerts[jira_key]` (e.g. `AXIS-101`)
    - `alerts[jira_status]` (`In Progress`, `Done`)
    - `alerts[message]` (Root-cause summary)

---

## 📐 3. Production DAX Measures Reference

Copy and paste these measures directly into Power BI Desktop via **Modeling > New Measure**:

```dax
// 1. Total Customer Feedback Volume
Total Reviews = COUNTROWS('reviews')

// 2. Chattermill Net Sentiment Score (NSS)
Net Sentiment Score = 
VAR PosCount = CALCULATE(COUNTROWS('sentiment_results'), 'sentiment_results'[polarity] = "Positive")
VAR NegCount = CALCULATE(COUNTROWS('sentiment_results'), 'sentiment_results'[polarity] = "Negative")
VAR TotalCount = COUNTROWS('sentiment_results')
RETURN
    IF(TotalCount > 0, DIVIDE(PosCount - NegCount, TotalCount, 0) * 100, 0)

// 3. Silent Churn / Rating Discrepancy Rate (%)
Discrepancy Rate = 
VAR DiscrepancyCount = CALCULATE(COUNTROWS('reviews'), 'reviews'[has_rating_discrepancy] = TRUE())
VAR TotalCount = COUNTROWS('reviews')
RETURN
    IF(TotalCount > 0, DIVIDE(DiscrepancyCount, TotalCount, 0) * 100, 0)

// 4. Total Alerts Count
Total Alerts = COUNTROWS('alerts')

// 5. Critical Control Limit Breaches Count
Critical Alerts = 
CALCULATE(
    COUNTROWS('alerts'),
    'alerts'[severity] = "CRITICAL"
)

// 6. Average Leave-One-Out (LOO) Star Drag
Avg Star Drag = AVERAGE('alerts'[star_impact])

// 7. Open JIRA Incidents (To Do or In Progress)
Open JIRA Tickets = 
CALCULATE(
    COUNTROWS('alerts'),
    'alerts'[jira_status] IN {"To Do", "In Progress"}
)

// 8. JIRA Resolution Rate (%)
JIRA Resolution Rate = 
VAR ResolvedTickets = CALCULATE(COUNTROWS('alerts'), 'alerts'[jira_status] = "Done")
VAR TotalTrackedTickets = CALCULATE(COUNTROWS('alerts'), NOT(ISBLANK('alerts'[jira_key])) && 'alerts'[jira_key] <> "")
RETURN
    IF(TotalTrackedTickets > 0, DIVIDE(ResolvedTickets, TotalTrackedTickets, 0) * 100, 0)
```

---

## 🔄 4. How to Refresh the Dashboard

### Step 1: Export Updated Telemetry
Run the export script from the repository root:
```bash
python scripts/export_bi_dataset.py
```
This updates the 4 CSV files in `powerbi/data/` with the latest review ingestion runs, statistical control limit breaches, and JIRA ticket statuses.

### Step 2: Refresh in Power BI Desktop
1. Open your report (`.pbix`) in **Power BI Desktop**.
2. Click the **Refresh** button on the **Home** ribbon tab.
3. Power BI will reload all updated rows from `powerbi/data/` and recalculate all visual metrics, NSS scores, and JIRA operational status gauges.
