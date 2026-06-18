# Project2Product AI 🚀

Project2Product AI is a self-contained, intelligent codebase analysis tool designed to scan, evaluate, and transform standard software repositories into monetization-ready SaaS (Software-as-a-Service) products. By scanning local ZIP uploads or cloning GitHub repositories, the system detects business domains, scores code complexity, suggests microservices, extracts API blueprints, and compiles printable PDF analysis reports.

---

## 🔍 Table of Contents
1. [Key Features](#-key-features)
2. [Project Architecture](#-project-architecture)
3. [Registering & Sign-Up Data Storage](#-registering--sign-up-data-storage)
4. [API Keys & External Integrations](#-api-keys--external-integrations)
5. [Getting Started (Run Locally)](#-getting-started-run-locally)

---

## 🚀 Key Features

* **Local Codebase Analyzer**: Accepts zip files or Git URLs, runs file-tree diagnostics, tracks language percentages, and scans AST patterns (classes, functions, routing, and DB models).
* **Heuristic Intelligence Engines**:
  * **Domain Detector**: Matches source keywords to categorize codebases into standard domains (e.g., Healthcare, FinTech, E-Commerce, Logistics, HR, CRM) with a confidence score.
  * **Product Scoring Engine**: Calculates code complexity, modularity, and overall SaaS-readiness.
  * **SaaS Recommender**: Formulates target audience definitions, pricing models (Tiers/SaaS features), and launch strategies.
  * **Microservice Engine**: Suggests decoupling strategies and lists potential microservice boundaries.
* **Interactive Architecture Visualizer**: Generates dynamic node-based diagrams using **React Flow** on the frontend, mapping proposed microservices.
* **PDF Report Generator**: Packages codebase intelligence into a downloadable, professionally formatted PDF report using `ReportLab`.
* **User Dashboard**: Visualizes overall analytics, language metrics, top-scoring projects, and aggregate API endpoints.

---

## 🏗️ Project Architecture

The application is built as a split-architecture monolith:

* **Backend**: Python FastAPI with SQLite for persistent storage, SQLAlchemy ORM, and bcrypt password hashing.
* **Frontend**: React + TypeScript + Vite, using Tailwind CSS for UI design, Lucide icons, Framer Motion for transitions, React Flow for diagrams, and Recharts for dashboard analytics.

```
projectToproduct/
├── backend/                  # FastAPI Application
│   ├── uploads/              # Temporal storage for zip extractions & Git clones
│   ├── api_extractor.py      # Rule-based API endpoint mapper
│   ├── auth.py               # Authentication helpers & JWT token logic
│   ├── database.py           # SQLite database engine connection
│   ├── domain_detector.py    # Keywords mapping logic
│   ├── main.py               # Main FastAPI routes & execution pipelines
│   ├── models.py             # SQLAlchemy schemas (Users, Projects, Analysis, Reports)
│   ├── report_generator.py   # ReportLab PDF building rules
│   └── ...                   # Custom heuristic modules (Business, SaaS, microservices, etc.)
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── pages/            # App Views (Dashboard, Upload, Auth, Reports, etc.)
│   │   ├── App.tsx           # Global Router & Auth context provider
│   │   └── index.css         # Styling directives & Tailwind imports
│   └── package.json          # Frontend packages
└── requirements.txt          # Python dependencies
```

---

## 💾 Registering & Sign-Up Data Storage

All user registration and sign-up data is stored **locally** for privacy and self-containment.

* **Database Engine**: SQLite
* **Database File**: `project2product.db` (located in `backend/project2product.db`)
* **User Data Table**: `users`
* **Security & Hashing**: Passwords are secure and never stored in plain text. They are hashed using **bcrypt** via the Python `passlib` context before database commits.
* **Session Verification**: Stateless session verification is managed through JSON Web Tokens (JWT) signed locally using `python-jose`.

### User Database Schema (`models.py`)
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (Primary Key) | Auto-incrementing unique user identifier. |
| `email` | String (Unique, Indexed) | User's unique login email identifier. |
| `hashed_password` | String | Bcrypt-hashed password representation. |
| `fullname` | String (Nullable) | User's full name. |
| `created_at` | DateTime | Timestamp of user creation (UTC). |

---

## 🔑 API Keys & External Integrations

**There are NO external API keys required or utilized in this project.** 

* **100% Offline & Local**: All analysis engines, SaaS classifiers, and domain logic are implemented using **rules-based AST parsers and keyword dictionary heuristics** directly inside the Python backend.
* **No Third-Party Services**: The project does not connect to external AI services (like OpenAI, Anthropic, or Gemini) or external databases.
* **JWT Signing Key**: A local fallback key is specified in `backend/auth.py` for token signature:
  `SECRET_KEY = "p2p_ai_local_super_secret_key_which_should_be_changed"`

---

## 🛠️ Getting Started (Run Locally)

### 1. Start the Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Activate your virtual environment (if available) and install dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```
3. Run the FastAPI dev server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### 2. Start the Frontend
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
4. Access the web panel in your browser at `http://localhost:5173`.
