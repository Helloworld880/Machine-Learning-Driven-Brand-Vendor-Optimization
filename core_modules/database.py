import sqlite3
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
import random

from core_modules.auth import hash_password
from core_modules.config import Config

logger = logging.getLogger(__name__)

DB_PATH = "Data layer/vendors.db"


class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.data_dir = os.path.dirname(self.db_path)
        self.config = Config()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
        self._seed_if_empty()

    # ─────────────────────────────────────────────
    # INIT & SCHEMA
    # ─────────────────────────────────────────────
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            name        TEXT,
            email       TEXT,
            role        TEXT DEFAULT 'user',
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS vendors (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT,
            phone           TEXT,
            category        TEXT,
            status          TEXT DEFAULT 'Active',
            risk_level      TEXT DEFAULT 'Low',
            contract_value  REAL DEFAULT 0,
            rating          REAL DEFAULT 0,
            join_date       TEXT,
            country         TEXT DEFAULT 'USA'
        );

        CREATE TABLE IF NOT EXISTS performance_metrics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id       INTEGER NOT NULL,
            metric_date     TEXT NOT NULL,
            on_time_pct     REAL DEFAULT 0,
            defect_rate_pct REAL DEFAULT 0,
            cost_variance   REAL DEFAULT 0,
            quality_score   REAL DEFAULT 0,
            overall_score   REAL DEFAULT 0,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS financial_metrics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id       INTEGER NOT NULL,
            period          TEXT NOT NULL,
            category        TEXT,
            total_spend     REAL DEFAULT 0,
            cost_savings    REAL DEFAULT 0,
            invoice_count   INTEGER DEFAULT 0,
            payment_days    REAL DEFAULT 0,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS risk_assessments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id       INTEGER NOT NULL,
            assessment_date TEXT NOT NULL,
            financial_risk  REAL DEFAULT 0,
            operational_risk REAL DEFAULT 0,
            compliance_risk  REAL DEFAULT 0,
            overall_risk     REAL DEFAULT 0,
            risk_level       TEXT DEFAULT 'Low',
            mitigation_status TEXT DEFAULT 'Not Started',
            notes           TEXT,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS compliance_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id       INTEGER NOT NULL,
            audit_date      TEXT NOT NULL,
            compliance_status TEXT DEFAULT 'Under Review',
            audit_score     REAL DEFAULT 0,
            certifications  TEXT,
            next_audit_date TEXT,
            auditor         TEXT,
            findings        TEXT,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS email_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient   TEXT,
            subject     TEXT,
            body        TEXT,
            sent_at     TEXT,
            status      TEXT DEFAULT 'sent'
        );

        CREATE TABLE IF NOT EXISTS ml_predictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id       INTEGER NOT NULL,
            prediction_date TEXT NOT NULL,
            risk_score      REAL,
            churn_prob      REAL,
            performance_forecast REAL,
            model_version   TEXT DEFAULT 'v1.0',
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        );
        """)
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────
    # SEED DATA
    # ─────────────────────────────────────────────
    def _seed_if_empty(self):
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
        conn.close()
        if count == 0:
            self._seed_all()

    def _seed_all(self):
        random.seed(42)
        np.random.seed(42)

        categories = ["IT Services", "Logistics", "Manufacturing", "Consulting", "Raw Materials", "Marketing", "Facilities"]
        statuses = ["Active", "Active", "Active", "Inactive", "Under Review"]
        risk_levels = ["Low", "Low", "Medium", "Medium", "High"]
        countries = ["USA", "UK", "Germany", "India", "Canada", "Australia", "Japan"]
        
        vendor_names = [
            "TechCorp Inc", "Global Supplies Ltd", "Quality Parts Co", "Innovative Solutions",
            "Reliable Services LLC", "Prime Vendors Inc", "EcoTech Solutions", "Green Logistics",
            "Sustainable Mfg Co", "Ethical Consulting", "Clean Energy Partners", "Social Impact Corp",
            "Digital Dynamics", "Smart Systems Ltd", "NextGen Vendors", "Alpha Procurement",
            "BetaSupply Chain", "GammaTech Services", "Delta Consulting", "Epsilon Logistics"
        ]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Seed admin user
        pw_hash = hash_password(self.config.DEMO_ADMIN_PASSWORD)
        c.execute("""INSERT OR IGNORE INTO users (username,password,name,email,role,created_at)
                     VALUES (?,?,?,?,?,?)""",
                  (
                   self.config.DEMO_ADMIN_USERNAME,
                   pw_hash,
                   self.config.DEMO_ADMIN_NAME,
                   self.config.DEMO_ADMIN_EMAIL,
                   "admin",
                   datetime.now().isoformat()))

        vendor_ids = []
        for i, name in enumerate(vendor_names):
            cat = categories[i % len(categories)]
            status = statuses[i % len(statuses)]
            risk = risk_levels[i % len(risk_levels)]
            contract_val = round(random.uniform(50000, 500000), 2)
            rating = round(random.uniform(3.0, 5.0), 2)
            join_date = (datetime.now() - timedelta(days=random.randint(180, 1800))).strftime("%Y-%m-%d")
            country = countries[i % len(countries)]
            c.execute("""INSERT INTO vendors(name,email,phone,category,status,risk_level,
                         contract_value,rating,join_date,country) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                      (name, f"contact@{name.lower().replace(' ', '')}.com",
                       f"+1-555-{random.randint(1000,9999)}", cat, status, risk,
                       contract_val, rating, join_date, country))
            vendor_ids.append(c.lastrowid)

        # Performance metrics - last 12 months per vendor
        for vid in vendor_ids:
            for m in range(12):
                month_date = (datetime.now() - timedelta(days=30 * m)).strftime("%Y-%m-%d")
                on_time = round(random.uniform(75, 99), 2)
                defect = round(random.uniform(0.5, 8.0), 2)
                cost_var = round(random.uniform(-5, 10), 2)
                quality = round(random.uniform(70, 98), 2)
                overall = round((on_time * 0.4 + quality * 0.4 + (100 - defect * 10) * 0.2), 2)
                c.execute("""INSERT INTO performance_metrics
                             (vendor_id,metric_date,on_time_pct,defect_rate_pct,cost_variance,quality_score,overall_score)
                             VALUES (?,?,?,?,?,?,?)""",
                          (vid, month_date, on_time, defect, cost_var, quality, overall))

        # Financial metrics
        periods = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1"]
        for vid in vendor_ids:
            for period in periods:
                spend = round(random.uniform(10000, 80000), 2)
                savings = round(spend * random.uniform(0.05, 0.25), 2)
                c.execute("""INSERT INTO financial_metrics
                             (vendor_id,period,category,total_spend,cost_savings,invoice_count,payment_days)
                             VALUES (?,?,?,?,?,?,?)""",
                          (vid, period, categories[vid % len(categories)],
                           spend, savings, random.randint(5, 40), round(random.uniform(15, 60), 1)))

        # Risk assessments
        for vid in vendor_ids:
            fin_risk = round(random.uniform(10, 85), 2)
            ops_risk = round(random.uniform(10, 80), 2)
            comp_risk = round(random.uniform(5, 75), 2)
            overall = round((fin_risk + ops_risk + comp_risk) / 3, 2)
            level = "High" if overall >= 65 else "Medium" if overall >= 35 else "Low"
            c.execute("""INSERT INTO risk_assessments
                         (vendor_id,assessment_date,financial_risk,operational_risk,
                          compliance_risk,overall_risk,risk_level,mitigation_status)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (vid, datetime.now().strftime("%Y-%m-%d"),
                       fin_risk, ops_risk, comp_risk, overall, level,
                       random.choice(["Not Started", "In Progress", "Completed", "Monitoring"])))

        # Compliance records
        certs_pool = ["ISO 9001", "ISO 14001", "SOC 2", "ISO 27001", "HIPAA", "GDPR", "PCI DSS"]
        for vid in vendor_ids:
            audit_date = (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
            next_audit = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")
            audit_score = round(random.uniform(60, 100), 2)
            status = "Compliant" if audit_score >= 80 else "Under Review" if audit_score >= 65 else "Non-Compliant"
            certs = ", ".join(random.sample(certs_pool, random.randint(1, 3)))
            c.execute("""INSERT INTO compliance_records
                         (vendor_id,audit_date,compliance_status,audit_score,certifications,
                          next_audit_date,auditor,findings)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (vid, audit_date, status, audit_score, certs, next_audit,
                       f"Auditor {random.randint(1,5)}",
                       "No critical findings." if audit_score >= 80 else "Minor gaps identified."))

        conn.commit()
        conn.close()
        logger.info("✅ Database seeded with sample data.")

    def _csv_path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def _load_csv(self, filename: str) -> pd.DataFrame:
        path = self._csv_path(filename)
        if not os.path.exists(path):
            return pd.DataFrame()
        try:
            return pd.read_csv(path)
        except Exception as exc:
            logger.warning(f"Could not read CSV {filename}: {exc}")
            return pd.DataFrame()

    # ─────────────────────────────────────────────
    # VENDOR QUERIES
    # ─────────────────────────────────────────────
    def get_vendors(self):
        with sqlite3.connect(self.db_path) as conn:
            db_df = pd.read_sql_query("SELECT * FROM vendors", conn)

        csv_df = self._load_csv("vendors.csv")
        if csv_df.empty:
            return db_df

        csv_df = csv_df.rename(
            columns={
                "vendor_id": "id",
                "contact_email": "email",
                "contact_phone": "phone",
                "start_date": "join_date",
            }
        )
        csv_df["vendor_id"] = csv_df["id"]

        desired = ["id", "vendor_id", "name", "email", "phone", "category", "status", "risk_level", "contract_value", "rating", "join_date", "country"]
        for col in desired:
            if col not in csv_df.columns:
                csv_df[col] = None
        csv_df = csv_df[desired]

        if not db_df.empty:
            db_df = db_df.copy()
            db_df["vendor_id"] = db_df["id"]
            db_df = db_df[[col for col in desired if col in db_df.columns]]
            extras = db_df[~db_df["id"].isin(csv_df["id"])]
            if not extras.empty:
                csv_df = pd.concat([csv_df, extras], ignore_index=True)

        return csv_df.reset_index(drop=True)

    def get_vendors_with_performance(self):
        vendors = self.get_vendors()
        perf = self.get_performance_data()
        if vendors.empty:
            return pd.DataFrame()

        if perf.empty:
            result = vendors.rename(columns={"id": "vendor_id"}).copy()
            result["avg_performance"] = np.nan
            result["avg_on_time"] = np.nan
            result["avg_defect_rate"] = np.nan
            result["avg_quality"] = np.nan
            return result

        perf_agg = (
            perf.groupby("vendor_id", as_index=False)
            .agg(
                avg_performance=("overall_score", "mean"),
                avg_on_time=("on_time_pct", "mean"),
                avg_defect_rate=("defect_rate_pct", "mean"),
                avg_quality=("quality_score", "mean"),
            )
        )
        result = vendors.merge(perf_agg, left_on="id", right_on="vendor_id", how="left", suffixes=("", "_perf"))
        result["vendor_id"] = result["id"]

        risk = self.get_risk_data()
        if not risk.empty:
            risk_cols = [c for c in ["vendor_id", "risk_level", "overall_risk"] if c in risk.columns]
            risk_latest = risk[risk_cols].drop_duplicates("vendor_id", keep="last")
            result = result.drop(columns=["risk_level"], errors="ignore").merge(risk_latest, on="vendor_id", how="left")

        return result

    def add_vendor(self, name, email, phone, category, status="Active",
                   risk_level="Low", contract_value=0, rating=0, country="USA"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO vendors(name,email,phone,category,status,risk_level,
                            contract_value,rating,join_date,country) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                         (name, email, phone, category, status, risk_level,
                          contract_value, rating, datetime.now().strftime("%Y-%m-%d"), country))
            conn.commit()

    def update_vendor(self, vendor_id, **updates):
        allowed = {
            "name",
            "email",
            "phone",
            "category",
            "status",
            "risk_level",
            "contract_value",
            "rating",
            "country",
        }
        clean_updates = {key: value for key, value in updates.items() if key in allowed}
        if not clean_updates:
            return False

        assignments = ", ".join(f"{column} = ?" for column in clean_updates)
        values = list(clean_updates.values()) + [vendor_id]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE vendors SET {assignments} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0

    def delete_vendor(self, vendor_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM performance_metrics WHERE vendor_id = ?", (vendor_id,))
            conn.execute("DELETE FROM financial_metrics WHERE vendor_id = ?", (vendor_id,))
            conn.execute("DELETE FROM risk_assessments WHERE vendor_id = ?", (vendor_id,))
            conn.execute("DELETE FROM compliance_records WHERE vendor_id = ?", (vendor_id,))
            conn.execute("DELETE FROM ml_predictions WHERE vendor_id = ?", (vendor_id,))
            cursor = conn.execute("DELETE FROM vendors WHERE id = ?", (vendor_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ─────────────────────────────────────────────
    # PERFORMANCE QUERIES
    # ─────────────────────────────────────────────
    def get_performance_data(self):
        with sqlite3.connect(self.db_path) as conn:
            db_df = pd.read_sql_query("""
                SELECT pm.*, v.name AS vendor_name, v.category
                FROM performance_metrics pm
                JOIN vendors v ON pm.vendor_id = v.id
                ORDER BY pm.metric_date DESC
            """, conn)

        csv_df = self._load_csv("performance.csv")
        if csv_df.empty:
            return db_df

        csv_df = csv_df.rename(
            columns={
                "metric_id": "id",
                "on_time_delivery": "on_time_pct",
                "defect_rate": "defect_rate_pct",
            }
        )
        if "cost_variance" not in csv_df.columns:
            csv_df["cost_variance"] = np.nan
        desired = [
            "id",
            "vendor_id",
            "metric_date",
            "on_time_pct",
            "defect_rate_pct",
            "cost_variance",
            "quality_score",
            "overall_score",
            "vendor_name",
            "category",
        ]
        for col in desired:
            if col not in csv_df.columns:
                csv_df[col] = np.nan
        csv_df = csv_df[desired]

        if not db_df.empty:
            extras = db_df[~db_df["vendor_id"].isin(csv_df["vendor_id"].unique())]
            if not extras.empty:
                csv_df = pd.concat([csv_df, extras[desired]], ignore_index=True)

        return csv_df.sort_values("metric_date", ascending=False).reset_index(drop=True)

    def get_performance_trends(self):
        perf = self.get_performance_data()
        if perf.empty:
            return pd.DataFrame()
        return (
            perf.groupby("metric_date", as_index=False)
            .agg(
                avg_score=("overall_score", "mean"),
                avg_on_time=("on_time_pct", "mean"),
                avg_defect=("defect_rate_pct", "mean"),
            )
            .sort_values("metric_date")
        )

    # ─────────────────────────────────────────────
    # FINANCIAL QUERIES
    # ─────────────────────────────────────────────
    def get_financial_data(self):
        with sqlite3.connect(self.db_path) as conn:
            db_df = pd.read_sql_query("""
                SELECT fm.*, 
                       v.name AS vendor_name, 
                       v.category AS vendor_category
                FROM financial_metrics fm
                JOIN vendors v ON fm.vendor_id = v.id
                ORDER BY fm.period DESC
            """, conn)

        csv_df = self._load_csv("financial_metrics.csv")
        if csv_df.empty:
            return db_df

        csv_df = csv_df.rename(columns={"fin_id": "id", "category": "vendor_category"})
        desired = [
            "id",
            "vendor_id",
            "period",
            "vendor_category",
            "total_spend",
            "cost_savings",
            "vendor_name",
            "contract_value",
            "actual_cost",
            "cost_variance",
            "invoice_accuracy",
            "budget_utilization",
            "roi_score",
            "overdue_invoices",
            "discount_availed",
        ]
        for col in desired:
            if col not in csv_df.columns:
                csv_df[col] = np.nan
        csv_df = csv_df[desired]

        if not db_df.empty:
            db_df = db_df.copy()
            extras = db_df[~db_df["vendor_id"].isin(csv_df["vendor_id"].unique())]
            if not extras.empty:
                for col in desired:
                    if col not in extras.columns:
                        extras[col] = np.nan
                csv_df = pd.concat([csv_df, extras[desired]], ignore_index=True)

        return csv_df.sort_values("period", ascending=False).reset_index(drop=True)

    def get_financial_summary(self):
        fin = self.get_financial_data()
        if fin.empty:
            return pd.DataFrame()
        return (
            fin.groupby("vendor_category", as_index=False)
            .agg(
                total_spend=("total_spend", "sum"),
                cost_savings=("cost_savings", "sum"),
                vendor_count=("vendor_id", "nunique"),
            )
            .rename(columns={"vendor_category": "category"})
        )

    # RISK QUERIES
    # ─────────────────────────────────────────────
    def get_risk_history(self):
        csv_df = self._load_csv("risk_history.csv")
        if not csv_df.empty:
            if "vendor_id" not in csv_df.columns:
                logger.warning("risk_history.csv missing required column: vendor_id")
                return pd.DataFrame()

            vendors = self.get_vendors()[["id", "category", "contract_value"]].rename(columns={"id": "vendor_id"})
            csv_df = csv_df.merge(vendors, on="vendor_id", how="left")
            sort_cols = [c for c in ["vendor_id", "assessment_date"] if c in csv_df.columns]
            return csv_df.sort_values(sort_cols) if sort_cols else csv_df

        return pd.DataFrame()

    def get_risk_data(self):
        history = self.get_risk_history()
        if not history.empty:
            latest = (
                history.sort_values("assessment_date")
                .drop_duplicates("vendor_id", keep="last")
                .rename(columns={"risk_id": "id"})
                .sort_values("overall_risk", ascending=False)
            )
            return latest.reset_index(drop=True)

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("""
                SELECT r.*, v.name AS vendor_name, v.category, v.contract_value
                FROM risk_assessments r
                JOIN vendors v ON r.vendor_id = v.id
                ORDER BY r.overall_risk DESC
            """, conn)

    # ─────────────────────────────────────────────
    # COMPLIANCE QUERIES
    # ─────────────────────────────────────────────
    def get_compliance_history(self):
        csv_df = self._load_csv("compliance_history.csv")
        if not csv_df.empty:
            if "vendor_id" not in csv_df.columns:
                logger.warning("compliance_history.csv missing required column: vendor_id")
                return pd.DataFrame()

            vendors = self.get_vendors()[["id", "category"]].rename(columns={"id": "vendor_id"})
            csv_df = csv_df.merge(vendors, on="vendor_id", how="left")
            csv_df = csv_df.rename(columns={"compliance_id": "id", "compliance_score": "audit_score"})
            sort_cols = [c for c in ["vendor_id", "audit_date"] if c in csv_df.columns]
            return csv_df.sort_values(sort_cols) if sort_cols else csv_df

        return pd.DataFrame()

    def get_compliance_data(self):
        history = self.get_compliance_history()
        if not history.empty:
            latest = (
                history.sort_values("audit_date")
                .drop_duplicates("vendor_id", keep="last")
                .sort_values("audit_score", ascending=True)
            )
            return latest.reset_index(drop=True)

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("""
                SELECT c.*, v.name AS vendor_name, v.category
                FROM compliance_records c
                JOIN vendors v ON c.vendor_id = v.id
                ORDER BY c.audit_score ASC
            """, conn)

    def get_vendor_outcomes(self):
        return self._load_csv("vendor_outcomes.csv")

    # ─────────────────────────────────────────────
    # ML PREDICTIONS
    # ─────────────────────────────────────────────
    def save_ml_predictions(self, vendor_id, risk_score, churn_prob, perf_forecast, model_version="v2.0"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO ml_predictions
                (vendor_id,prediction_date,risk_score,churn_prob,performance_forecast,model_version)
                VALUES (?,?,?,?,?,?)""",
                         (vendor_id, datetime.now().strftime("%Y-%m-%d"),
                          risk_score, churn_prob, perf_forecast, model_version))
            conn.commit()

    def get_ml_predictions(self):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("""
                SELECT mp.*, v.name AS vendor_name, v.category, v.risk_level
                FROM ml_predictions mp
                JOIN vendors v ON mp.vendor_id = v.id
                ORDER BY mp.prediction_date DESC
            """, conn)

    # ─────────────────────────────────────────────
    # USER AUTH
    # ─────────────────────────────────────────────
    def get_user(self, username):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row:
            cols = ["id", "username", "password", "name", "email", "role", "created_at"]
            return dict(zip(cols, row))
        return None

    def log_email(self, recipient, subject, body="", status="sent"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO email_logs(recipient,subject,body,sent_at,status)
                            VALUES (?,?,?,?,?)""",
                         (recipient, subject, body, datetime.now().isoformat(), status))
            conn.commit()
