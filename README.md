<p align="center">
  <img src="frontend/public/parakh-logo.png" alt="PARAKH Logo" width="480" />
</p>

# PARAKH &bull; MPLADS AI Vigilance & Intelligence Platform
### Autonomous Anomaly Detection, Geospatial Risk Diagnostics & Grounded LLM Auditing

> **PARAKH (परख)**: *An AI-powered vigilance, geospatial analytics, and decision-support platform designed to monitor, audit, and safeguard public funds allocated under the Member of Parliament Local Area Development Scheme (MPLADS).*

---

## 🌟 Executive Summary

The **PARAKH AI Vigilance Platform** is an enterprise-grade monitoring and audit system built for the **Ministry of Statistics and Programme Implementation (MoSPI)**, State Nodal Departments, District Authorities, and Central Vigilance Officers.

By analyzing authentic MPLADS data across Parliamentary Constituencies, PARAKH automatically surfaces:
1. **Cost Escalations & Overruns** (expenditures exceeding administratively sanctioned limits).
2. **Critical Timeline Backlogs** (prolonged delays relative to scheduled completion milestones).
3. **Financial vs. Physical Progress Mismatches** (disproportionate disbursements with little to no ground execution).
4. **Disproportionate Payment Spikes** (front-loaded fund releases prior to physical milestones).
5. **Semantic & Spatial Duplicate Works** (overlapping sanctions for identical or near-identical physical infrastructure within the same geographic cluster).
6. **Geographic Hotspots** (density-based anomaly clusters across specific districts or agencies).
7. **Multivariate Unsupervised Outliers** (via Isolation Forest models).
8. **Supervised ML Risk Classification** (benchmarking Logistic Regression, Random Forest, XGBoost, and LightGBM).
9. **Grounded AI Auditing** (powered by Google Gemini 3.5 Flash Lite with zero hallucination and strict grounding against verified official scheme data).

---

## 🛡️ Responsible AI & Ethical Design

- **Investigative Support, Not Automated Accusation**: The system never issues definitive criminal conclusions. Instead, it classifies projects as *Potential Anomaly*, *High-Risk Project*, *Potential Duplicate*, *Requires Field Verification*, or *Audit Recommended*.
- **Demographic Neutrality**: Caste, religion, ethnicity, and gender are completely excluded from all feature sets, schemas, and models.
- **Political Impartiality**: MP identity and party affiliation are strictly excluded as predictive features in fraud-risk calculations.
- **Zero Hallucination Standard**: The integrated Gemini LLM query engine operates under strict factual grounding guidelines—queries outside the scope of MPLADS are declined, and unrecorded project information is clearly stated as unavailable rather than fabricated.

---

## 🏗️ Technology Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PARAKH FULL-STACK ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
 ┌────────────────────────────────────────────────────────┐
 │  FRONTEND CLIENT (React 18 + Vite + Tailwind CSS)     │
 │  - Real-time Leaflet GIS Map with Risk Pulsating Pins  │
 │  - Recharts Visualizations & Anomaly Distributions     │
 │  - Floating Grounded Gemini AI Assistant Widget        │
 │  - In-flight Request Deduplication & Memory Cache      │
 └───────────────────────┬────────────────────────────────┘
                         │ REST / JSON (HTTP/Gzip)
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │  FASTAPI BACKEND CORE (Python 3.12)                   │
 │  - Multi-Factor Rule Engine & Risk Scorer              │
 │  - Geospatial Haversine & Spatial Proximity Engine     │
 │  - NLP Semantic Matching (TF-IDF + Cosine Similarity)  │
 │  - Isolation Forest Unsupervised Anomaly Detector      │
 │  - Supervised Model Suite (XGBoost, LightGBM, RF, LR)  │
 │  - Grounded Gemini LLM Audit Engine                    │
 └───────────────────────┬────────────────────────────────┘
                         │ SQLAlchemy 2.0
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │  PERSISTENCE & STORAGE LAYER                           │
 │  - PostgreSQL 16 + PostGIS (Production)                │
 │  - SQLite with WAL & Composite Indexes (Local Dev)     │
 │  - 4,320+ Authentic Master Records + 95,964 Archive    │
 └────────────────────────────────────────────────────────┘
```

| Layer | Technologies & Tools |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts, React-Leaflet, Leaflet |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn, Bcrypt, PyJWT |
| **AI & LLM** | Google Gemini (`gemini-3.5-flash-lite`), Strict Grounding Engine |
| **Machine Learning** | scikit-learn, XGBoost, LightGBM, Isolation Forest, TF-IDF NLP Similarity |
| **Database** | PostgreSQL 16 + PostGIS 3.4 (Production) / SQLite (Zero-setup Local) |
| **DevOps & Serving** | Docker, Docker Compose, Nginx (Gzip level 6, Asset Caching) |

---

## 🚀 Key Modules & Capabilities

### 1. Interactive High-Performance GIS Map
- **Precise Geocoding**: Visualizes projects at their exact district and constituency coordinates.
- **Dynamic Risk Categorization**: Critical (red pulsating with twinkle animations), High (amber), Medium (yellow), and Low (emerald) markers.
- **Dual Clustered Views**: Macro state-level cluster bubbles with instant drill-down to individual project pins.
- **Spatial Duplicate Links**: Visualizes detected duplicate works or double-billing candidates with dashed purple link lines (filtered to realistic physical proximity &le; 25 km).
- **High-Throughput Rendering**: Capable of streaming and rendering up to 100,000 markers with seamless panning and zooming.

### 2. Grounded Gemini AI Query Engine
- **Model**: Powered by Google Gemini 3.5 Flash Lite (`gemini-3.5-flash-lite`).
- **Grounded Verification**: Directly references official scheme attributes: sanctioned amount, expenditure, physical milestone progress, implementing agency, and GPS coordinates.
- **Zero Hallucination**: Explicitly declines non-MPLADS queries and informs the investigator when a record is not in the official database.
- **Multi-Surface Access**: Available both via the persistent Floating AI Widget and project detail pages.

### 3. Multi-Model ML Anomaly Detection
- **Rule-Based Engine**: Computes deterministic risk points based on configurable thresholds (Cost Overrun %, Progress Gap %, Delay Days, Payment Pace).
- **Unsupervised Isolation Forest**: Identifies multivariate statistical outliers across financial and temporal dimensions without human labeling bias.
- **Supervised Model Comparison**: Evaluates and benchmarks Logistic Regression, Random Forest, XGBoost, and LightGBM with live ROC-AUC, Precision, Recall, and Confusion Matrices.

### 4. Semantic & Spatial Duplicate Detection
- Identifies ghost works and potential double-billing by comparing project work descriptions using TF-IDF vectorization and cosine similarity combined with Haversine distance calculations.

### 5. Performance Optimizations
- **Composite Database Indexes**: Optimized indexes on `(risk_level, overall_score)`, `(state, district)`, and expenditure columns—reducing API query latency from 1.8s to ~140ms.
- **Nginx Gzip Compression**: Real-time compression at level 6 across JSON, CSS, and JS assets, achieving up to 21x bandwidth reduction.
- **Client Cache & Deduplication**: High-speed memory cache (`apiCache`) with TTL and request deduplication to eliminate redundant network roundtrips during navigation.

---

## 💻 Quick Start Guide

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**
- *(Recommended)* **Docker & Docker Compose**

---

### Method 1: Docker Compose (Full Stack - Recommended)

The simplest way to run the entire stack (PostgreSQL + PostGIS, FastAPI, and Nginx React):

1. **Clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/PARAKH.git
   cd PARAKH
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```
   *(Optional: Add your Google Gemini API key to `.env` to enable live LLM queries)*

3. **Launch Containers**:
   ```bash
   docker compose up --build
   ```

4. **Access the Applications**:
   - **Frontend Web Portal**: [http://localhost:3000](http://localhost:3000)
   - **FastAPI Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Database (PostgreSQL / PostGIS)**: `localhost:5432`

---

### Method 2: Local Development Run

#### 1. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI backend with hot-reload
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup (in a separate terminal)
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```

Open your browser at: **http://localhost:5173**

---

## 👤 Evaluator Quick-Login Demo Accounts

You can log in instantly using the role pills on the login screen or enter the credentials below:

| Role | Email | Password | Permissions & Capabilities |
|---|---|---|---|
| **Investigator** | `investigator@mplads.gov.in` | `Investigator@123` | Case triage, evidence audit, inspector note taking |
| **Analyst** | `analyst@mplads.gov.in` | `Analyst@123` | ML model benchmarking, threshold sandbox simulation |
| **Admin** | `admin@mplads.gov.in` | `Admin@123` | Full system access, data ingestion & dataset reset |
| **Viewer** | `viewer@mplads.gov.in` | `Viewer@123` | Read-only executive dashboard & GIS visualizer |

---

## 🧪 Automated Testing Suite

Verify backend API endpoints, ML models, duplicate detectors, and frontend builds:

```bash
# Run backend pytest test suite
PYTHONPATH=backend pytest backend/tests/ -v

# Run frontend TypeScript type-check and production build
cd frontend && npm run build
```

---

## 📁 Repository Structure

```
PARAKH/
├── backend/                    # FastAPI Python Backend Service
│   ├── app/
│   │   ├── api/                # API Endpoints (projects, gis, ai, alerts, duplicates, ml, ingestion)
│   │   ├── core/               # Configuration, security, JWT authentication, RBAC
│   │   ├── db/                 # Database schema models & SQLAlchemy connection
│   │   ├── schemas/            # Pydantic request/response validation models
│   │   ├── services/           # ML models, rule engine, isolation forest, duplicate detector, Gemini LLM
│   │   └── main.py             # FastAPI entrypoint & application lifespan
│   ├── tests/                  # Pytest test suite
│   └── requirements.txt        # Backend dependencies
├── frontend/                   # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/         # Reusable UI widgets (GIS Map, Sidebar, Floating AI Widget, etc.)
│   │   ├── context/            # Authentication & Role context provider
│   │   ├── pages/              # Dashboard, GIS Map, Project Explorer, Analytics, Risk Center, etc.
│   │   ├── services/           # Typed API service layer with request deduplication & memory cache
│   │   ├── types/              # TypeScript interface definitions
│   │   ├── App.tsx             # Root application & routing
│   │   └── main.tsx            # React application mount
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts          # Vite build config with manual chunk splitting
├── docker/                     # Container configurations
│   ├── Dockerfile.backend      # Python 3.12 Slim production backend
│   ├── Dockerfile.frontend     # Multi-stage Node builder + Nginx production server
│   └── nginx.conf              # Nginx reverse proxy with Gzip level 6 & static caching
├── docs/                       # Architectural & design documentation
│   ├── ARCHITECTURE.md
│   └── RESPONSIBLE_AI.md
├── Data/                       # Reference datasets & coordinate lookups
│   └── district_coordinates.csv # District-level GPS coordinates lookup
├── docker-compose.yml          # Multi-container orchestration (PostGIS, Backend, Frontend)
├── .env.example                # Sample environment configuration template
└── README.md                   # Comprehensive project documentation
```

---

## 🏛️ Attribution & Disclaimer
Developed for the **Smart India Hackathon** under the problem statement:
*"Development of an AI-powered system to detect anomalies, fraud, and inefficiencies in MPLAD Scheme implementation."*

*Disclaimer: PARAKH is designed as a vigilance decision-support system. Risk metrics and flags generated by the platform represent potential anomalies that warrant review and do not constitute formal legal judgments.*
