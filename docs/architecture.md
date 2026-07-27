# BrandGuard Architecture

## System Diagram (Conceptual)

```
[Sources: CSV datasets / CSV Uploads]
        │
        ▼
[Ingestion Service] — backend/app/ingestion/
        │
        ▼
[NLP/ABSA Enrichment Service] — backend/app/ml/absa/
        │
        ▼
[SQLModel / SQLAlchemy ORM Layer] — backend/app/models/
        │
        ▼
[Postgres Database + pgvector] — Store metadata & embeddings
        │
        ▼
[FastAPI Serving Layer] — backend/app/api/
        │
        ▼
[Streamlit Frontend Dashboard] — Interactive visual dashboard
```

## Folder Structure Mapping

* **`backend/app/api/`**: Router paths for endpoints.
* **`backend/app/core/`**: Logging configurations, Pydantic settings loading `.env` variables.
* **`backend/app/db/`**: Alembic database migrations and session setup.
* **`backend/app/models/`**: SQLModel DB declarations (Review, Product, Aspect, SentimentResult).
* **`backend/app/schemas/`**: Pydantic validation schemas.
* **`backend/app/services/`**: Core business/orchestration logic.
* **`backend/app/ml/`**: Machine Learning pipeline packages.
  * **`absa/`**: Aspect-Based Sentiment Analysis modules (DistilBERT + heuristics).
  * **`embeddings/`**: Embedding pipeline module (sentence-transformers).
  * **`rag/`**: Retrieval-Augmented Generation module for "Ask BrandGuard" queries.
  * **`eval/`**: Model validation evaluation harness scripts.
* **`frontend/`**: Streamlit application UI.
* **`data/`**: Raw datasets (Amazon reviews) and processed cache tables.
* **`scripts/`**: One-off CSV/JSON loader commands.
