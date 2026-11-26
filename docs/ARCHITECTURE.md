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

    subgraph RAW_LS["1A. Lok Sabha Source Files (Data/Lok-Shaba • 112 MB)"]
        LS_REC["Works Recommended.csv\n102,339 records (31.26 MB)"]:::source
        LS_SANC["Works Sanctioned.csv\n77,472 records (25.69 MB)"]:::source
        LS_EXP["Expenditure on Works.csv\n81,706 records (19.56 MB)"]:::source
        LS_COMP["Works Completed.csv\n33,667 records (10.24 MB)"]:::source
        LS_LIM["Allocated Limit MPs.csv\n544 records"]:::source
    end

    subgraph RAW_RS["1B. Rajya Sabha Source Files (Data/Rajya-Shaba • 25 MB)"]
        RS_REC["Works Recommended.csv\n24,540 records (8.43 MB)"]:::source
        RS_SANC["Works Sanctioned.csv\n19,079 records (7.07 MB)"]:::source
        RS_EXP["Expenditure on Works.csv\n24,749 records (6.60 MB)"]:::source
        RS_COMP["Works Completed.csv\n9,831 records (3.35 MB)"]:::source
        RS_LIM["Allocated Limit MPs.csv\n222 records"]:::source
    end

    subgraph GEO_REF["1C. Geospatial Master Reference"]
        DIST_GEO["district_coordinates.csv\n732 District GPS Centroid Coordinates"]:::source
    end

    subgraph ETL["2. Ingestion & Spatial Geocoding Pipeline"]
        INGEST_SCRIPT["ingest_all_data_folder.py\nSchema Normalization, Multi-File Reconciliation & Key Joins"]:::etl
        GEO_SCRIPT["recalculate_exact_coordinates.py\n732 District Coordinate Centroid Lookup & Locality Offsets"]:::etl
    end

    subgraph STORAGE["3. Production Persistence Layer (mplads.db • SQLite WAL Mode)"]
        TBL_PROJ["projects (95,964 rows)\nID, Title, Category, State, District, GPS Coordinates, Dates"]:::db
        TBL_FIN["financial_records (69,852 rows)\nSanctioned Cost, Total Expenditure, Fund Releases"]:::db
        TBL_PROG["progress_records (95,964 rows)\nPhysical Progress %, Delay Days, Status: Completed/Ongoing"]:::db
        TBL_RISK["risk_scores (95,964 rows)\nOverall Score (0-100), Level (LOW/MED/HIGH/CRIT), Rationales"]:::db
        TBL_ALERT["alerts (10,228 rows)\nCost Overrun, Milestone Delay, Duplicate Flag, Unsanctioned Work"]:::db
        TBL_DUP["duplicate_candidates (1,000 rows)\nPair Matches, Cosine Similarity %, Haversine Distance km"]:::db
        TBL_MODELS["model_runs (4 rows)\nLogistic Regression, Random Forest, XGBoost, LightGBM Metrics"]:::db
    end

    subgraph ENGINES["4. Analytics, Machine Learning & AI Intelligence Suite"]
        ENG_RULE["Deterministic Statutory Rule Engine (rule_engine.py)\nCost Overruns, Milestone Delays, High Spend vs Low Progress"]:::engine
        ENG_ISO["Unsupervised Anomaly Model (isolation_forest.py)\nIsolation Forest (100 estimators, 15% contamination rate)"]:::engine
        ENG_DUP["NLP & Geospatial Duplicate Detector (duplicate_detector.py)\nTF-IDF N-Grams (Cosine Sim >= 0.85) + Haversine (<= 25km)"]:::engine
        ENG_BENCH["Supervised ML Benchmark Suite (supervised_models.py)\nXGBoost, LightGBM, Random Forest, Logistic Regression (5-Fold CV)"]:::engine
        ENG_LLM["Grounded AI Auditing Assistant (ai_query_engine.py)\nGoogle Gemini 3.5 Flash Lite + Anti-Hallucination SQL Grounding"]:::engine
    end

    subgraph API_LAYER["5. Gateway & API Service (FastAPI on Render Cloud)"]
        FASTAPI["FastAPI Backend (parakh-backend-qj54.onrender.com)\nREST Endpoints, SQLite WAL Gzip Boot Extraction, JWT Auth, 4-Tier RBAC"]:::api
    end

    subgraph CLIENT_LAYER["6. Client Presentation & Visualization (Vercel Global Edge CDN)"]
        REACT_APP["React 18 + Vite Web App (parakh-lyart-one.vercel.app)\nInteractive Leaflet GIS Map (4,320+ Pins), Recharts KPIs, AI Assistant"]:::ui
    end

    RAW_LS -->|102k Recom / 77k Sanc| INGEST_SCRIPT
    RAW_RS -->|24k Recom / 19k Sanc| INGEST_SCRIPT
    GEO_REF -->|732 District GPS| GEO_SCRIPT
    INGEST_SCRIPT -->|95,964 Normalized Records| STORAGE
    GEO_SCRIPT -->|Pinpoint Coordinates| STORAGE
    STORAGE -->|Feature Extraction| ENGINES
    ENGINES -->|Risk Ratings & Alerts| STORAGE
    STORAGE -->|Indexed SQL Queries| FASTAPI
    FASTAPI -->|REST API / JSON Payloads| REACT_APP
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
