import sqlite3
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

DB_PATH = "Data layer/vendors.db"


class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH
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

        CREATE TABLE IF NOT EXISTS brand_metrics (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name              TEXT NOT NULL,
            sustainability_score    REAL DEFAULT 0,
            social_impact_score     REAL DEFAULT 0,
            governance_score        REAL DEFAULT 0,
            environmental_score     REAL DEFAULT 0,
            carbon_footprint        REAL DEFAULT 0,
            renewable_energy_pct    REAL DEFAULT 0,
            updated_at              TEXT
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
        import hashlib
        pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""INSERT OR IGNORE INTO users (username,password,name,email,role,created_at)
                     VALUES (?,?,?,?,?,?)""",
                  ("admin", pw_hash, "Administrator", "admin@company.com", "admin",
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

        # Brand metrics
        brand_data = [
            ("EcoTech Solutions", 88, 85, 90, 92, 120, 85),
            ("Green Logistics", 92, 78, 85, 89, 180, 65),
            ("Sustainable Mfg Co", 85, 82, 88, 83, 320, 45),
            ("Ethical Consulting", 79, 91, 92, 75, 95, 90),
            ("Clean Energy Partners", 95, 87, 84, 96, 65, 95),
            ("Social Impact Corp", 82, 94, 89, 80, 110, 75),
            ("Digital Dynamics", 76, 79, 81, 78, 280, 35),
            ("Smart Systems Ltd", 89, 83, 86, 91, 150, 70),
        ]
        for bd in brand_data:
            c.execute("""INSERT INTO brand_metrics
                         (brand_name,sustainability_score,social_impact_score,governance_score,
                          environmental_score,carbon_footprint,renewable_energy_pct,updated_at)
                         VALUES (?,?,?,?,?,?,?,?)""",
                      (*bd, datetime.now().strftime("%Y-%m-%d")))

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

    # ─────────────────────────────────────────────
    # VENDOR QUERIES
    # ─────────────────────────────────────────────
    def get_vendors(self):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("SELECT * FROM vendors", conn)

    def get_vendors_with_performance(self):
        query = """
        SELECT v.id AS vendor_id, v.name, v.category, v.status, v.risk_level,
               v.contract_value, v.rating, v.country,
               AVG(pm.overall_score)   AS avg_performance,
               AVG(pm.on_time_pct)     AS avg_on_time,
               AVG(pm.defect_rate_pct) AS avg_defect_rate,
               AVG(pm.quality_score)   AS avg_quality
        FROM vendors v
        LEFT JOIN performance_metrics pm ON v.id = pm.vendor_id
        GROUP BY v.id
        """
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn)

    def add_vendor(self, name, email, phone, category, status="Active",
                   risk_level="Low", contract_value=0, rating=0, country="USA"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO vendors(name,email,phone,category,status,risk_level,
                            contract_value,rating,join_date,country) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                         (name, email, phone, category, status, risk_level,
                          contract_value, rating, datetime.now().strftime("%Y-%m-%d"), country))
            conn.commit()

    # ─────────────────────────────────────────────
    # PERFORMANCE QUERIES
    # ─────────────────────────────────────────────
    def get_performance_data(self):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("""
                SELECT pm.*, v.name AS vendor_name, v.category
                FROM performance_metrics pm
                JOIN vendors v ON pm.vendor_id = v.id
                ORDER BY pm.metric_date DESC
            """, conn)

    def get_performance_trends(self):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("""
                SELECT metric_date, AVG(overall_score) AS avg_score,
                       AVG(on_time_pct) AS avg_on_time,
                       AVG(defect_rate_pct) AS avg_defect
                FROM performance_metrics
                GROUP BY metric_date
                ORDER BY metric_date
            """, conn)

    # ─────────────────────────────────────────────
    # FINANCIAL QUERIES
    # ─────────────────────────────────────────────
    def get_financial_data(self):
     with sqlite3.connect(self.db_path) as conn:
        return pd.read_sql_query("""
            SELECT fm.*, 
                   v.name AS vendor_name, 
                   v.category AS vendor_category
            FROM financial_metrics fm
            JOIN vendors v ON fm.vendor_id = v.id
            ORDER BY fm.period DESC
        """, conn)

    def get_financial_summary(self):
     with sqlite3.connect(self.db_path) as conn:
        return pd.read_sql_query("""
            SELECT fm.category,
                   SUM(fm.total_spend)   AS total_spend,
                   SUM(fm.cost_savings)  AS cost_savings,
                   COUNT(DISTINCT fm.vendor_id) AS vendor_count,
                   AVG(fm.payment_days)  AS avg_payment_days
            FROM financial_metrics fm
            JOIN vendors v ON fm.vendor_id = v.id
            GROUP BY fm.category
        """, conn)

    # ─────────────────────────────────────────────
    # BRAND / ESG QUERIES
    # ─────────────────────────────────────────────
    def get_brand_metrics(self):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("SELECT * FROM brand_metrics", conn)

    def add_brand_metric(self, brand_name, sustainability, social, governance,
                         environmental=0, carbon=0, renewable=0):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO brand_metrics
                (brand_name,sustainability_score,social_impact_score,governance_score,
                 environmental_score,carbon_footprint,renewable_energy_pct,updated_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                         (brand_name, sustainability, social, governance,
                          environmental, carbon, renewable, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()

    # ─────────────────────────────────────────────
    # RISK QUERIES
    # ─────────────────────────────────────────────
    def get_risk_data(self):
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
    def get_compliance_data(self):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query("""
                SELECT c.*, v.name AS vendor_name, v.category
                FROM compliance_records c
                JOIN vendors v ON c.vendor_id = v.id
                ORDER BY c.audit_score ASC
            """, conn)

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