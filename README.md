# 🛡️ BrandGuard: AI-Powered Review Intelligence Hub

> *"In a world overflowing with opinions, BrandGuard turns chaos into clarity."*

---

## 🎯 Project Overview

BrandGuard is a decision-grade review intelligence dashboard. It ingests customer reviews, processes them using a custom Aspect-Based Sentiment Analysis (ABSA) model (DistilBERT + heuristics), extracts top keywords/pros/cons, and provides interactive analytics and natural language Q&A (RAG search) to reveal what customers actually think about specific product attributes.

---

## ⚙️ Tech Stack

| Layer | Technologies |
|:---|:---|
| **Language** | Python 3.11+ |
| **API Backend** | FastAPI + Pydantic v2 + Uvicorn |
| **Database & Search** | PostgreSQL 15 + `pgvector` extension |
| **Background Services**| Redis 7 |
| **NLP Pipeline** | PyTorch + Hugging Face Transformers (DistilBERT + BART-large-CNN) |
| **Analytics/BI** | Pandas, NumPy, Plotly |
| **Testing & Quality** | Pytest, Black, Ruff, Isort, Pre-Commit |
| **Deployment** | Docker & Docker Compose |

---

## 📂 Project Structure

```
brandguard/
├── pyproject.toml            # Dependencies and packaging setup
├── docker-compose.yml        # PostgreSQL + pgvector + Redis services
├── Makefile                  # Utility commands for the local workflow
├── backend/
│   ├── app/                  # Application source
│   │   ├── api/routes/       # REST API endpoints
│   │   ├── core/             # Configuration & logging settings
│   │   ├── ml/absa/          # Sentiment and aspect extractors
│   │   ├── main.py           # App entrypoint
│   │   └── ...
│   └── tests/                # Unit and integration test suites
├── data/                     # Raw review datasets (gitignored)
├── docs/                     # Spec blueprints and build specs
└── frontend/                 # Streamlit UI dashboard
```

---

## 🚀 Getting Started

### 📋 Prerequisites

1. Install **Python 3.11+**
2. Install **Docker Desktop** (required to run PostgreSQL + pgvector local instance)

### 🛠️ Local Development Setup

1. **Clone the repository** (if not already done)
2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install the package in editable mode with development dependencies**:
   ```bash
   pip install -e ".[dev,ml]"
   ```
4. **Copy environmental config template**:
   ```bash
   copy .env.example .env
   ```
5. **Launch local database and cache services via Docker**:
   ```bash
   docker-compose up -d
   ```
6. **Start the FastAPI application**:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
   *The API will run at [http://localhost:8000](http://localhost:8000) and the auto-generated documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).*

---

## 🧪 Testing and Formatting

You can use the standard CLI tools or run them via the `Makefile` helper commands:

* **Format the code**: `make format`
* **Check styling and formats**: `make lint`
* **Run tests**: `make test`
