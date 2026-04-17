<div align="center">

# 🏢 Vendor Insight 360

**A production-grade vendor analytics platform for tracking performance, financials, risk, and compliance — powered by AI.**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-Educational-green?style=flat-square)](#license)

[Features](#-features) · [Tech Stack](#-tech-stack) · [Project Structure](#-project-structure) · [Setup](#-setup) · [AI Features](#-ai-features) · [Automation](#-automation) · [Reports](#-reports)

---

![Dashboard Preview](https://img.shields.io/badge/Dashboard-Streamlit%20%7C%20Plotly-FF4B4B?style=for-the-badge&logo=streamlit)

</div>

---

## 📌 Overview

**Vendor Insight 360** is a full-stack vendor management analytics platform built with Python and Streamlit. It gives procurement teams, vendor managers, and executives a single dashboard to monitor all vendor relationships — from financial performance and delivery KPIs to compliance audits and AI-generated risk explanations.

The platform ships with a **realistic demo dataset generator** (120 vendors × 24 months) so dashboards and reports are immediately believable on first run, without any real data.

---

## ✨ Features

| Module | What it does |
|---|---|
| 📊 **Vendor Performance** | KPIs, delivery trends, SLA compliance across all vendors |
| 💰 **Financial Analytics** | Spend tracking, variance analysis, overdue flags, ROI signals |
| ⚠️ **Risk Management** | Portfolio-level risk view, vendor drill-down, trend movement |
| ✅ **Compliance** | Audit scores, compliance history, status tracking per vendor |
| 📄 **Reports** | Generate PDF, Excel, and HTML reports on demand |
| 🤖 **AI Insights** | Ask questions over vendor data, executive summaries, alert explanations |
| ⚙️ **Automation** | Alert monitoring + scheduled report generation scripts |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **UI / Dashboard** | [Streamlit](https://streamlit.io) |
| **Charts** | [Plotly](https://plotly.com/python/) · [Matplotlib](https://matplotlib.org) |
| **Database** | SQLite (via `vendors.db`) |
| **AI / LLM** | Claude API (Anthropic) — with safe fallback if key not set |
| **ML** | scikit-learn (clustering, risk scoring, predictive analytics) |
| **Reports** | ReportLab (PDF) · openpyxl (Excel) · Jinja2 (HTML) |
| **Testing** | Pytest |
| **Language** | Python 3.9+ |

---

## 📁 Project Structure

```
Vendor-Insight-360/
│
├── app.py                          # Streamlit entry point
├── run.py                          # CLI runner
├── run_api.py                      # API server runner
├── setup.py
├── requirements.txt
├── pytest.ini
├── create_dataset.bat              # Windows shortcut to regenerate demo data
├── DATASET_IMPROVEMENT_PLAN.md
│
├── core_modules/                   # Core business logic
│   ├── analytics.py                # Vendor KPI calculations
│   ├── api.py                      # Internal API layer
│   ├── auth.py                     # JWT authentication
│   ├── config.py                   # App configuration
│   ├── database.py                 # SQLite connection + queries
│   ├── email_service.py            # Alert email delivery
│   ├── import_dataset.py           # CSV → DB importer
│   ├── ml_engine.py                # ML scoring pipeline
│   ├── realistic_dataset.py        # Demo data generator
│   ├── risk_model.py               # Risk scoring logic
│   └── vendor_clustering.py        # Vendor segmentation (k-means)
│
├── enhancements/                   # Advanced analytics modules
│   ├── benchmarking.py             # Industry benchmark comparisons
│   ├── ml_engine.py                # Enhanced ML pipeline
│   └── report_generator.py         # PDF / Excel / HTML generation
│
├── ui_pages/                       # Streamlit page modules
│   ├── ai_page.py                  # 🤖 AI Insights page
│   ├── reports_page.py             # Report generation UI
│   ├── risk_page.py                # Risk management UI
│   └── settings_page.py            # App settings + re-seed
│
├── data_layer/                     # Data files
│   ├── vendors.csv
│   ├── performance.csv
│   ├── financial_metrics.csv
│   ├── risk_history.csv
│   ├── compliance_history.csv
│   ├── vendor_outcomes.csv
│   ├── industry_benchmarks.csv
│   └── vendors.db                  # SQLite database
│
├── WORKFLOWS & AUTOMATION/
│   ├── scripts/
│   │   ├── alert_monitor.py        # Threshold breach detector
│   │   └── report_scheduler.py     # Scheduled report runner
│   └── workflows/
│       ├── vendor_onboarding.yaml
│       ├── performance_review.yaml
│       └── issue_escalation.yaml
│
├── tests/
│   └── test_data_health.py
│
├── reports/                        # Manual report outputs
└── generated_reports/              # Automated report outputs
```

---

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/Helloworld880/Vendor-Insight-360.git
cd Vendor-Insight-360
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Set your AI API key

For AI features to work, add your Anthropic API key as an environment variable:

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="your-key-here"

# Windows
set ANTHROPIC_API_KEY=your-key-here
```

> **Note:** The app works without a key — AI features gracefully fall back to rule-based outputs.

### 4. Generate the demo dataset

```bash
python -c "
from core_modules.realistic_dataset import DatasetSpec, write_to_data_layer
print(write_to_data_layer('data_layer', DatasetSpec(n_vendors=120, months=24, start_month='2024-01-01', seed=42), overwrite=True))
"
```

Or use **Settings → Re-seed Database** from inside the running app.

### 5. Run the dashboard

```bash
streamlit run app.py
```

Open in your browser: [http://localhost:8501](http://localhost:8501)

---

## 🤖 AI Features

The `ui_pages/ai_page.py` module provides three AI-powered capabilities:

### Ask Data
Type a plain English question about your vendor data and get an instant answer — no SQL required.

```
"Which vendors have the worst compliance score this quarter?"
"Show me vendors with delivery performance below 80% in the last 6 months."
"What are the top 5 vendors by spend in the Technology category?"
```

### Executive Summary
Automatically generates a 3–5 sentence board-ready summary of the entire vendor portfolio — performance trends, risk concentrations, and recommended actions.

### Alert Explanations
When the alert monitor fires, AI explains each breach in plain English and suggests a next action, turning raw threshold alerts into something a vendor manager can immediately act on.

> All AI features use the Claude API (`claude-sonnet-4-6`). If no API key is set, the app falls back to rule-based summaries automatically.

---

## ⚙️ Automation

### Alert Monitor

Scans all vendor KPIs against configured thresholds and fires alerts when breaches are detected. Supports dry-run mode for testing.

```bash
# Safe dry run (no emails sent)
python "WORKFLOWS & AUTOMATION/scripts/alert_monitor.py" --dry-run

# Live run
python "WORKFLOWS & AUTOMATION/scripts/alert_monitor.py"
```

### Report Scheduler

Runs continuously in the background and generates reports on a schedule. Supports daily (`08:00`) and weekly (`monday 09:00`) patterns configured in YAML.

```bash
python "WORKFLOWS & AUTOMATION/scripts/report_scheduler.py" --run
```

### Workflow YAML

Automation workflows are defined declaratively in YAML:

| Workflow | Description |
|---|---|
| `vendor_onboarding.yaml` | Steps + checks when a new vendor is added |
| `performance_review.yaml` | Periodic review triggers and escalation rules |
| `issue_escalation.yaml` | Auto-escalation when SLAs are repeatedly missed |

---

## 📄 Reports

Reports can be generated from the **Reports** page in the dashboard, or triggered automatically by the scheduler.

| Format | Description |
|---|---|
| **PDF** | Printable vendor performance + compliance report |
| **Excel** | Raw data + pivot-ready sheets for further analysis |
| **HTML** | Interactive web report viewable in any browser |

Reports are saved to:

```
reports/           ← manually triggered
generated_reports/ ← scheduler output
```

---

## 🧪 Tests

```bash
pytest tests/
```

The test suite validates data health — ensuring CSVs and the SQLite database are consistent and no vendor records have missing critical fields.

---

## 🗺 Roadmap

- [x] Vendor performance KPI dashboard
- [x] Financial analytics + risk scoring
- [x] PDF / Excel / HTML report generation
- [x] AI "Ask Data" chat interface
- [x] Automated alert monitoring
- [x] Realistic demo dataset generator
- [ ] Role-based access control (RBAC)
- [ ] Cloud deployment (Docker + AWS/GCP)
- [ ] Real-time data ingestion pipeline
- [ ] Mobile-optimised dashboard
- [ ] ERP integration (SAP / Oracle connectors)

---

## 👤 Author

**Yash Dudhani**

[![GitHub](https://img.shields.io/badge/GitHub-Helloworld880-181717?style=flat-square&logo=github)](https://github.com/Helloworld880)

---

## 📝 License

This project is intended for **educational and research purposes**.

---

<div align="center">
  <sub>Built with Python · Streamlit · SQLite · Claude AI</sub>
</div>
