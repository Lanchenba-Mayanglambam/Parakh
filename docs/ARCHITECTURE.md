# Technical Architecture Documentation

## System Topology & Data Flow

PARAKH operates on an authentic, end-to-end data pipeline built on verified **Ministry of Statistics and Programme Implementation (MoSPI)** public datasets. Below is the exact architectural topology mapping raw source files, automated ETL scripts, database row counts, machine learning engines, and live production endpoints.

```mermaid
flowchart TD
    classDef source fill:#FEF2F2,stroke:#EF4444,stroke-width:2px,color:#991B1B;
    classDef etl fill:#FFFBEB,stroke:#F59E0B,stroke-width:2px,color:#92400E;
    classDef db fill:#F0FDF4,stroke:#10B981,stroke-width:2px,color:#065F46;
    classDef engine fill:#EEF2FF,stroke:#6366F1,stroke-width:2px,color:#3730A3;
    classDef api fill:#FAF5FF,stroke:#A855F7,stroke-width:2px,color:#6B21A8;
    classDef ui fill:#F0F9FF,stroke:#0284C7,stroke-width:2px,color:#075985;

    subgraph RAW["1. Authentic MoSPI Source Datasets (Data/ Directory • 365,000+ Raw Rows • ~138 MB)"]
        direction LR
        subgraph LS["Lok Sabha Records (112 MB)"]
            LS_REC["Works Recommended.csv<br/>102,339 records"]:::source
            LS_SANC["Works Sanctioned.csv<br/>77,472 records"]:::source
            LS_EXP["Expenditure on Works.csv<br/>81,706 records"]:::source
            LS_COMP["Works Completed.csv<br/>33,667 records"]:::source
            LS_LIM["Allocated Limit MPs.csv<br/>544 records"]:::source
        end
        subgraph RS["Rajya Sabha Records (25 MB)"]
            RS_REC["Works Recommended.csv<br/>24,540 records"]:::source
            RS_SANC["Works Sanctioned.csv<br/>19,079 records"]:::source
            RS_EXP["Expenditure on Works.csv<br/>24,749 records"]:::source
            RS_COMP["Works Completed.csv<br/>9,831 records"]:::source
            RS_LIM["Allocated Limit MPs.csv<br/>222 records"]:::source
        end
        subgraph GEO_REF["Geospatial Master Reference"]
            DIST_GEO["district_coordinates.csv<br/>732 District GPS Centroids"]:::source
        end
    end

    subgraph ETL["2. Ingestion & Spatial Geocoding Pipeline"]
        INGEST_SCRIPT["ingest_all_data_folder.py<br/>• Schema Normalization & Deduplication<br/>• Composite Key Matching: Work ID + District + MP<br/>• Financial & Milestone Alignment"]:::etl
        GEO_SCRIPT["recalculate_exact_coordinates.py<br/>• 732 District Coordinate Centroid Lookup<br/>• Landmark & Locality Pinpointing (LOCALITY_LOOKUP)<br/>• Jitter Offset for Micro-Constituency Separation"]:::etl
    end

    subgraph STORAGE["3. Production Persistence Layer (mplads.db • SQLite WAL Mode • 95,964 Master Records)"]
        direction TB
        TBL_PROJ["projects (95,964 rows)<br/>ID, Title, Category, State, District, GPS Coordinates, Dates"]:::db
        TBL_FIN["financial_records (69,852 rows)<br/>Sanctioned Cost, Total Expenditure, Fund Releases, Financial %"]:::db
        TBL_PROG["progress_records (95,964 rows)<br/>Physical Progress %, Delay Days, Status: Completed/Ongoing"]:::db
        TBL_RISK["risk_scores (95,964 rows)<br/>Overall Score (0-100), Level (LOW/MED/HIGH/CRIT), Rationale"]:::db
        TBL_ALERT["alerts (10,228 rows)<br/>Cost Overrun, Milestone Delay, Duplicate Flag, Unsanctioned Work"]:::db
        TBL_DUP["duplicate_candidates (1,000 rows)<br/>Pair Matches, Cosine Similarity %, Haversine Distance km"]:::db
        TBL_MODELS["model_runs (4 rows)<br/>Logistic Regression, Random Forest, XGBoost, LightGBM Metrics"]:::db
    end

    subgraph ENGINES["4. Analytics, Machine Learning & AI Intelligence Suite"]
        direction TB
        ENG_RULE["Deterministic Statutory Rule Engine (rule_engine.py)<br/>• Cost Escalation: Expenditure > Sanctioned (> 100% / > 120%)<br/>• Milestone Delay: Schedule Overrun (> 180 / > 365 Days)<br/>• Fund Pace: High Spend (> 80%) vs Minimal Ground Progress (< 20%)<br/>• Unsanctioned Execution Detection"]:::engine
        ENG_ISO["Unsupervised Anomaly Model (isolation_forest.py)<br/>• Isolation Forest (n_estimators=100, contamination=0.15)<br/>• Multivariate Outlier Scoring on Financial-Temporal Feature Vectors"]:::engine
        ENG_DUP["NLP & Geospatial Duplicate Detector (duplicate_detector.py)<br/>• TF-IDF 2-4 Character & Word N-Grams (Cosine Sim >= 0.85)<br/>• Haversine Distance Geodesic Filter (<= 25.0 km Proximity Radius)"]:::engine
        ENG_BENCH["Supervised ML Benchmark Suite (supervised_models.py)<br/>• XGBoost, LightGBM, Random Forest, Logistic Regression<br/>• 5-Fold Stratified Cross-Validation, ROC-AUC, Confusion Matrix"]:::engine
        ENG_LLM["Grounded AI Auditing Assistant (ai_query_engine.py)<br/>• Google Gemini 3.5 Flash Lite with Zero-Hallucination Guardrails<br/>• Dynamic SQL Retrieval Context from 95,964 Ground-Truth Records"]:::engine
    end

    subgraph API_LAYER["5. Gateway & API Service (FastAPI on Render Cloud)"]
        direction TB
        FASTAPI["FastAPI Application (app/main.py)<br/>• Live URL: parakh-backend-qj54.onrender.com<br/>• REST Endpoints: /api/v1/projects, /gis/markers, /risk, /ai, /alerts<br/>• SQLite WAL Mode with Auto-Gzip Archive Extraction (mplads.db.gz)<br/>• JWT Bearer Authentication & 4-Tier RBAC (Admin, Analyst, Investigator, Viewer)<br/>• In-Memory Response Caching & Composite Indexing (ix_projects_risk_overall)"]:::api
    end

    subgraph CLIENT_LAYER["6. Client Presentation & Visualization (Vercel Global Edge CDN)"]
        direction TB
        REACT_APP["React 18 + TypeScript + Vite + Tailwind CSS (app.parakh)<br/>• Live URL: parakh-lyart-one.vercel.app<br/>• Interactive GIS Map (Leaflet Canvas: 4,320+ Rendered Markers & Duplicate Links)<br/>• Executive Analytics Dashboard (Recharts KPI Metrics & Risk Histograms)<br/>• Grounded AI Assistant Floating Widget (Markdown Streaming & Project Links)<br/>• Investigation Triage Center (Kanban Review Workflow & Audit Trail)"]:::ui
    end

    RAW -->|Raw CSV Data Pipeline| ETL
    ETL -->|Structured Ingestion & Coordinates| STORAGE
    STORAGE -->|ORM Feature Extraction| ENGINES
    ENGINES -->|Risk Scoring & Anomaly Flags| STORAGE
    STORAGE <-->|High-Speed SQL Queries| FASTAPI
    FASTAPI <-->|HTTPS / REST / JSON (JWT Protected)| REACT_APP
```

---

### Verified Data Ingestion & Integrity Metrics

| Category | Source File / Database Entity | Raw Record Count | File Size / Target Entity | Status & Description |
|---|---|---|---|---|
| **Lok Sabha Source** | `Data/Lok-Shaba/Works Recommended.csv` | **102,339** | 31.26 MB | Official recommended works ledger |
| **Lok Sabha Source** | `Data/Lok-Shaba/Works Sanctioned.csv` | **77,472** | 25.69 MB | Administratively sanctioned works |
| **Lok Sabha Source** | `Data/Lok-Shaba/Expenditure on Completed...csv` | **81,706** | 19.56 MB | Financial expenditure disbursements |
| **Lok Sabha Source** | `Data/Lok-Shaba/Works Completed.csv` | **33,667** | 10.24 MB | Physically completed works audit |
| **Lok Sabha Source** | `Data/Lok-Shaba/Allocated Limit for Honble MPs.csv` | **544** | 0.03 MB | MP constitutional fund ceilings |
| **Rajya Sabha Source** | `Data/Rajya-Shaba/Works Recommended.csv` | **24,540** | 8.43 MB | Upper House recommended works |
| **Rajya Sabha Source** | `Data/Rajya-Shaba/Works Sanctioned.csv` | **19,079** | 7.07 MB | Upper House sanctioned works |
| **Rajya Sabha Source** | `Data/Rajya-Shaba/Expenditure on Completed...csv` | **24,749** | 6.60 MB | Upper House financial expenditure |
| **Rajya Sabha Source** | `Data/Rajya-Shaba/Works Completed.csv` | **9,831** | 3.35 MB | Upper House completed works |
| **Rajya Sabha Source** | `Data/Rajya-Shaba/Allocated Limit for Honble MPs.csv` | **222** | 0.02 MB | State-wise MP fund ceilings |
| **Geospatial Master** | `Data/district_coordinates.csv` | **732** | 39.3 KB | Centroid GPS coordinates for all 732 Indian Districts |
| **Production Table** | `projects` (`mplads.db`) | **95,964** rows | Database Table | Unified scheme works with coordinates & metadata |
| **Production Table** | `financial_records` (`mplads.db`) | **69,852** rows | Database Table | Reconciled cost, sanction, and disbursement rows |
| **Production Table** | `progress_records` (`mplads.db`) | **95,964** rows | Database Table | Physical execution percentages and delay tracking |
| **Production Table** | `risk_scores` (`mplads.db`) | **95,964** rows | Database Table | Composite risk ratings and analytical rationales |
| **Production Table** | `alerts` (`mplads.db`) | **10,228** rows | Database Table | Actionable flags for overruns, delays, and duplicates |
| **Production Table** | `duplicate_candidates` (`mplads.db`) | **1,000** rows | Database Table | Detected duplicate pairs (similarity >= 0.85, dist <= 25km) |
| **Production Table** | `model_runs` (`mplads.db`) | **4** rows | Database Table | Benchmarked ML models (LR, RF, XGBoost, LightGBM) |

---

## Component Specifications

### 1. Backend Engine (`/backend/app`)
- **FastAPI Core**: Asynchronous ASGI framework providing OpenAPI schema documentation, CORS control, and sub-second response times.
- **SQLAlchemy 2.0 ORM**: Type-safe relational mappings for Projects, Financial Records, Progress Records, Agencies, Risk Scores, Alerts, and Audit Logs.
- **Authentication & RBAC**: JWT Bearer tokens with bcrypt password hashing and 4-tier role enforcement (`ADMIN`, `ANALYST`, `INVESTIGATOR`, `VIEWER`).

### 2. Machine Learning & Anomaly Detection Pipeline (`/backend/app/services/ml`)
1. **Deterministic Rule Engine (`rule_engine.py`)**:
   - Evaluates hard legal and procedural thresholds:
     - Cost escalation (>20% warning, >50% critical)
     - Progress gap (Financial % - Physical % > 20% warning, >40% critical)
     - Timeline delay (>60 days warning, >180 days critical)
     - Disproportionate payment paces (>60% spent with <30% physical completion)
2. **Unsupervised Isolation Forest (`isolation_forest.py`)**:
   - Engineered features: Cost escalation ratio, progress mismatch, delay days, planned duration, expenditure per physical progress percentage, and expenditure burn rates.
   - Computes multivariate anomaly scores without requiring pre-existing fraud labels.
3. **Supervised Classifier Benchmarking (`supervised_models.py`)**:
   - Evaluates 4 candidate algorithms via Stratified 5-Fold Cross-Validation:
     1. Logistic Regression
     2. Random Forest
     3. XGBoost
     4. LightGBM
   - Computes Precision, Recall, F1-Score, ROC-AUC, 2x2 Confusion Matrices, and Gini Feature Importances.
   - Automatically selects and activates the best-performing model.
4. **Duplicate Project Detector (`duplicate_detector.py`)**:
   - Hybrid NLP semantic similarity (TF-IDF character & word n-grams + cosine similarity) combined with spatial geodesic proximity (Haversine formula).
   - Generates duplicate match probability scores (0-100%) and actionable inspection recommendations.
5. **Explainable Risk Engine (`risk_engine.py`)**:
   - Synthesizes all components into a weighted composite score (0-100) mapped to `LOW` (0-30), `MEDIUM` (31-60), `HIGH` (61-80), and `CRITICAL` (81-100) with bulleted human-readable rationales.

### 3. Frontend Architecture (`/frontend/src`)
- **Executive Dashboard**: Interactive KPI summary cards, Recharts risk donut, state-wise expenditure & risk distribution bar charts, delay histograms, and anomaly category breakdown.
- **Project Explorer**: Full-featured searchable data grid with multi-parameter filtering, progress visualizers, and CSV export.
- **Interactive GIS Map**: React-Leaflet with OpenStreetMap tiles, custom color-coded risk markers with pulsing critical indicators, marker clustering, anomaly hotspot circles, and duplicate vector link lines.
- **Project Detail Deep Dive**:
  - Executive summary & agency card
  - Financial overview (Sanctioned, Released, Expended)
  - Physical vs Financial progress comparison gauges
  - **Interactive Visual Timeline**: Recommendation &rarr; Sanction &rarr; Fund Release &rarr; Work Start &rarr; Payment Milestones &rarr; Physical Updates &rarr; Current Status
  - Multi-factor risk radar & explainable AI bullet breakdown
  - Active alerts list with one-click case triage modal
  - Potential duplicate candidate cards
- **Investigation Center**: Triage Kanban pipeline (`NEW`, `UNDER_REVIEW`, `INVESTIGATION_RECOMMENDED`, `RESOLVED`, `DISMISSED`) with inspector notes and audit trail.
- **Model Analytics**: Live model comparison benchmark table, ROC-AUC metrics, confusion matrices, and feature importance bar chart.
- **Controlled AI Assistant**: Natural language query router interpreting domain questions without raw LLM SQL execution.
- **Data Ingestion Hub**: Drag-and-drop CSV/Excel uploader, real-time multi-field normalization, Data Quality Health score meter, and demo dataset reset.
