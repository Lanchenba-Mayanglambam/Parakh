<p align="center">
  <img src="frontend/public/parakh-logo.png" alt="PARAKH Logo" width="480" />
</p>

# PARAKH &bull; MPLADS AI Vigilance & Intelligence Platform
### Autonomous Anomaly Detection, Geospatial Risk Diagnostics & Grounded LLM Auditing

> **PARAKH (परख)**: *An AI-powered vigilance, geospatial analytics, and decision-support platform designed to monitor, audit, and safeguard public funds allocated under the Member of Parliament Local Area Development Scheme (MPLADS).*

---

## 🌐 Live Production Deployment

| Service | Platform | Live URL |
|---|---|---|
| **Web Portal** | **Vercel** | [https://parakh-lyart-one.vercel.app](https://parakh-lyart-one.vercel.app) |
| **Backend REST API** | **Render** | [https://parakh-backend-qj54.onrender.com](https://parakh-backend-qj54.onrender.com) |
| **Swagger API Docs** | **Render** | [https://parakh-backend-qj54.onrender.com/docs](https://parakh-backend-qj54.onrender.com/docs) |
| **GitHub Repository** | **GitHub** | [https://github.com/Lanchenba-Mayanglambam/Parakh](https://github.com/Lanchenba-Mayanglambam/Parakh) |

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

```mermaid
flowchart TD
    classDef client fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef gateway fill:#F5F3FF,stroke:#8B5CF6,stroke-width:2px,color:#4C1D95;
    classDef core fill:#ECFDF5,stroke:#10B981,stroke-width:2px,color:#064E3B;
    classDef engine fill:#FEF3C7,stroke:#F59E0B,stroke-width:2px,color:#78350F;
    classDef data fill:#FDF2F8,stroke:#EC4899,stroke-width:2px,color:#831843;

    subgraph CLIENT["1. Presentation & Client Layer (React 18 + Vite + Tailwind CSS)"]
        UI_GIS["Interactive GIS Map\n(Leaflet Engine + Pulsating Markers)"]:::client
        UI_DASH["Executive Analytics & KPIs\n(Recharts + Financial Gauges)"]:::client
        UI_AI["Floating AI Assistant\n(Grounded Gemini LLM Widget)"]:::client
        UI_TRIAGE["Investigation Center\n(Case Triage & Audit Trail)"]:::client
        UI_CACHE["Client Cache & Deduplication\n(In-Flight Promise Cache)"]:::client
    end

    subgraph GATEWAY["2. Security & Edge Delivery Layer"]
        VERCEL["Vercel Global Edge Network\n(SPA Rewrites & Static Asset CDN)"]:::gateway
        NGINX["Nginx Production Proxy\n(Gzip Level 6 + HTTP/2)"]:::gateway
        AUTH["Security & Auth Guard\n(JWT Bearer Tokens + 4-Tier RBAC)"]:::gateway
    end

    subgraph BACKEND["3. Backend Intelligence Core (FastAPI on Render / Python 3.12)"]
        API_ROUTER["API Routing & Controllers\n(Projects, GIS Markers, Risk, AI, Alerts)"]:::core

        subgraph ENGINES["Multi-Model Analytical & ML Suite"]
            RULE_ENG["Deterministic Rule Engine\n(Cost Overruns, Delays, Payment Paces)"]:::engine
            GEO_ENG["Geospatial Spatial Engine\n(Haversine Math + 2km Cluster Rings)"]:::engine
            DUP_ENG["NLP Duplicate Detector\n(TF-IDF N-Grams + Cosine Similarity)"]:::engine
            ISO_ENG["Unsupervised Anomaly Model\n(Isolation Forest Outlier Detection)"]:::engine
            ML_SUITE["Supervised ML Benchmark Suite\n(XGBoost, LightGBM, Random Forest, LR)"]:::engine
            LLM_ENG["Grounded Gemini AI Engine\n(gemini-3.5-flash-lite + Guardrails)"]:::engine
        end
    end

    subgraph STORAGE["4. Persistence & Storage Layer"]
        DB_SQLITE["SQLite with WAL Mode\n(High-Speed Local & Cloud Instance)"]:::data
        DB_POSTGIS["PostgreSQL 16 + PostGIS 3.4\n(Spatial GiST Coordinates Indexing)"]:::data
        DATA_ARCHIVE["Master Scheme Data Archive\n(4,320+ Live Records / 95,964 Works)"]:::data
    end

    CLIENT -->|HTTPS / REST / JSON| GATEWAY
    GATEWAY -->|Authenticated Requests| API_ROUTER
    API_ROUTER --> ENGINES
    ENGINES -->|SQLAlchemy 2.0 ORM| STORAGE
```

### 🔄 End-to-End Operational & Auditing Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Vigilance Officer / User
    participant Frontend as Web Client (Vercel)
    participant Backend as FastAPI Backend (Render)
    participant ML as ML & Rule Engine
    participant Gemini as Google Gemini 3.5 LLM
    participant Database as Database (PostGIS / SQLite)

    Officer->>Frontend: Accesses Portal & Selects Role
    Frontend->>Backend: POST /api/v1/auth/demo-login (JWT Auth)
    Backend-->>Frontend: Returns Auth Token & Role Permissions

    Officer->>Frontend: Opens GIS Map / Project Explorer
    Frontend->>Backend: GET /api/v1/projects/gis/markers?limit=5000
    Backend->>Database: Query projects with composite index
    Database-->>Backend: 4,320+ Geocoded Records
    Backend-->>Frontend: GeoJSON with Risk Severity Badges
    Frontend->>Officer: Renders High-FPS Canvas with Pulsating Pins

    Officer->>Frontend: Asks Question in AI Assistant
    Frontend->>Backend: POST /api/v1/ai/query
    Backend->>Database: Fetch verified scheme records
    Database-->>Backend: Grounded Project Facts & History
    Backend->>Gemini: Prompt with strict anti-hallucination context
    Gemini-->>Backend: Grounded Markdown Summary & Analysis
    Backend-->>Frontend: Markdown Response & Direct Project Links
    Frontend->>Officer: Displays Verified Audit Answer
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
   git clone https://github.com/Lanchenba-Mayanglambam/Parakh.git
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

## 🏛️ Disclaimer
*PARAKH is an autonomous vigilance decision-support platform designed for monitoring, auditing, and detecting anomalies and inefficiencies in MPLAD Scheme implementation. Risk metrics and flags generated by the platform represent potential anomalies that warrant review and do not constitute formal legal judgments.*
