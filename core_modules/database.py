import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


class DatabaseManager:
    def __init__(self):
        self.db_path = "Data layer/vendors.db"
        self.init_database()

    def init_database(self):
        """Initialize database with all required tables"""
        if not os.path.exists("Data layer"):
            os.makedirs("Data layer")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Vendors table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            join_date TEXT,
            total_sales REAL DEFAULT 0,
            rating REAL DEFAULT 0
        )
        """)

        # Products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock INTEGER,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        )
        """)

        # Transactions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_amount REAL,
            date TEXT,
            FOREIGN KEY(vendor_id) REFERENCES vendors(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """)

        # ESG (Environment, Social, Governance) metrics
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS brand_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            sustainability_score REAL,
            social_impact_score REAL,
            governance_score REAL,
            updated_at TEXT
        )
        """)

        # Cost savings analytics table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cost_savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            cost_savings REAL,
            recorded_at TEXT
        )
        """)

        # Email logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT,
            subject TEXT,
            sent_at TEXT
        )
        """)

        conn.commit()
        conn.close()

        # -------------------------------------------------
    # DATA ACCESS FOR REPORT GENERATOR
    # -------------------------------------------------
    def get_vendors_with_performance(self):
        """Combine vendors.csv and performance.csv for reporting."""
        import pandas as pd
        import os

        base_path = "Data layer"
        vendors_csv = os.path.join(base_path, "vendors.csv")
        performance_csv = os.path.join(base_path, "performance.csv")

        # If CSV files don't exist, return empty
        if not os.path.exists(vendors_csv):
            return pd.DataFrame()

        vendors = pd.read_csv(vendors_csv)

        if os.path.exists(performance_csv):
            performance = pd.read_csv(performance_csv)
            # Merge on vendor name if columns match
            if "name" in vendors.columns and "vendor_name" in performance.columns:
                vendors = vendors.merge(performance, left_on="name", right_on="vendor_name", how="left")
            else:
                vendors = pd.concat([vendors, performance], axis=1)

        # Add a default risk level and performance_score if missing
        if "risk_level" not in vendors.columns:
            vendors["risk_level"] = vendors["rating"].apply(
                lambda r: "Low" if r >= 4 else "Medium" if r >= 2 else "High"
            )
        if "performance_score" not in vendors.columns:
            vendors["performance_score"] = vendors.get("rating", 0) * 20  # e.g., rating 4 → 80%

        return vendors

    def get_financial_data(self):
        """Load financial metrics or cost savings data for reports."""
        import pandas as pd
        import os

        base_path = "Data layer"
        fm_csv = os.path.join(base_path, "financial_metrics.csv")
        savings_csv = os.path.join(base_path, "cost_savings.csv")

        if os.path.exists(fm_csv):
            return pd.read_csv(fm_csv)
        elif os.path.exists(savings_csv):
            return pd.read_csv(savings_csv)
        else:
            return pd.DataFrame()


    # -----------------------------
    # Core CRUD & Data Access
    # -----------------------------
    def add_vendor(self, name, email, phone):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO vendors (name, email, phone, join_date)
        VALUES (?, ?, ?, ?)
        """, (name, email, phone, join_date))

        conn.commit()
        conn.close()

    def get_vendors(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM vendors", conn)
        conn.close()
        return df

    def add_product(self, vendor_id, name, category, price, stock):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO products (vendor_id, name, category, price, stock)
        VALUES (?, ?, ?, ?, ?)
        """, (vendor_id, name, category, price, stock))
        conn.commit()
        conn.close()

    def get_products(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()
        return df

    def record_transaction(self, vendor_id, product_id, quantity, total_amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO transactions (vendor_id, product_id, quantity, total_amount, date)
        VALUES (?, ?, ?, ?, ?)
        """, (vendor_id, product_id, quantity, total_amount, date))
        conn.commit()
        conn.close()

    def get_transactions(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
        SELECT t.id, v.name AS vendor_name, p.name AS product_name, 
               t.quantity, t.total_amount, t.date
        FROM transactions t
        LEFT JOIN vendors v ON t.vendor_id = v.id
        LEFT JOIN products p ON t.product_id = p.id
        """, conn)
        conn.close()
        return df

    # -----------------------------
    # ESG and Analytics Queries
    # -----------------------------
    def get_brand_metrics(self):
        """Fetch ESG brand analytics safely"""
        conn = sqlite3.connect(self.db_path)
        try:
            query = "SELECT * FROM brand_metrics"
            df = pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"[ERROR] Unable to load brand_metrics: {e}")
            df = pd.DataFrame(columns=[
                "brand_name", "sustainability_score",
                "social_impact_score", "governance_score", "updated_at"
            ])
        conn.close()
        return df

    def add_brand_metric(self, brand_name, sustainability, social, governance):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO brand_metrics (brand_name, sustainability_score, social_impact_score, governance_score, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """, (brand_name, sustainability, social, governance, updated_at))
        conn.commit()
        conn.close()

    def get_cost_savings(self):
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM cost_savings", conn)
        except Exception:
            df = pd.DataFrame(columns=["category", "cost_savings", "recorded_at"])
        conn.close()
        return df

    def add_cost_saving(self, category, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        recorded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO cost_savings (category, cost_savings, recorded_at)
        VALUES (?, ?, ?)
        """, (category, amount, recorded_at))
        conn.commit()
        conn.close()

    # -----------------------------
    # Email logging
    # -----------------------------
    def log_email(self, recipient, subject):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO email_logs (recipient, subject, sent_at)
        VALUES (?, ?, ?)
        """, (recipient, subject, sent_at))
        conn.commit()
        conn.close()

    def get_email_logs(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM email_logs", conn)
        conn.close()
        return df

    # -----------------------------
    # Vendor Performance Data
    # -----------------------------
    def get_vendors_with_performance(self):
        """
        Return vendors with aggregated performance & sales metrics.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            query = """
            SELECT 
                v.id AS vendor_id,
                v.name,
                v.email,
                v.phone,
                IFNULL(SUM(t.total_amount), 0) AS total_sales,
                IFNULL(v.rating, 0) AS performance_score
            FROM vendors v
            LEFT JOIN transactions t ON v.id = t.vendor_id
            GROUP BY v.id, v.name
            """
            df = pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"[ERROR] Could not fetch vendor performance: {e}")
            df = pd.DataFrame(columns=["vendor_id", "name", "email", "phone", "total_sales", "performance_score"])
        finally:
            conn.close()
        return df


# -----------------------------
# Manual test or seeding helper
# -----------------------------
if __name__ == "__main__":
    db = DatabaseManager()
    print("✅ Database initialized successfully!")
    # -------------------------------------------------
    # FINANCIAL DATA SUPPORT (Used by ReportGenerator)
    # -------------------------------------------------
    def get_financial_data(self):
        """Return financial metrics for reports (from financial_metrics or cost_savings table)."""
        import sqlite3
        import pandas as pd

        conn = sqlite3.connect(self.db_path)
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)["name"].tolist()

        df = pd.DataFrame()

        # Priority: use financial_metrics if available
        if "financial_metrics" in tables:
            df = pd.read_sql_query("SELECT * FROM financial_metrics", conn)

        # Fallback: use cost_savings if financial_metrics not found
        elif "cost_savings" in tables:
            df = pd.read_sql_query("SELECT * FROM cost_savings", conn)

        conn.close()
        return df

    # Seed a few brand metrics if empty
    if db.get_brand_metrics().empty:
        db.add_brand_metric("EcoWear", 85.6, 78.2, 90.3)
        db.add_brand_metric("GreenGoods", 88.1, 82.4, 85.0)
        db.add_brand_metric("PlanetCare", 92.3, 80.0, 88.7)
        print("🌱 Seeded brand_metrics table with sample data.")
