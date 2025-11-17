import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

class AnalyticsEngine:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)

    # -------------------------------------------------
    # Vendor Performance Metrics
    # -------------------------------------------------
    def calculate_average_performance(self):
        """Calculate average vendor performance score"""
        try:
            df = self.db.get_vendors_with_performance()
            if df.empty:
                return 0.0
            return df['performance_score'].mean()
        except Exception as e:
            self.logger.error(f"Error calculating average performance: {e}")
            return 0.0

    def get_high_risk_vendors_count(self):
        """Count high-risk vendors"""
        try:
            df = self.db.get_risk_data()
            if df.empty:
                return 0
            if 'risk_level' in df.columns:
                return len(df[df['risk_level'].str.lower() == 'high'])
            elif 'overall_risk' in df.columns:
                return len(df[df['overall_risk'] >= 70])  # threshold = 70%
            return 0
        except Exception as e:
            self.logger.error(f"Error counting high-risk vendors: {e}")
            return 0

    def get_performance_distribution(self):
        """Return distribution of performance scores"""
        try:
            df = self.db.get_vendors_with_performance()
            if df.empty:
                return pd.DataFrame()
            return df[['vendor_id', 'name', 'performance_score']]
        except Exception as e:
            self.logger.error(f"Error generating performance distribution: {e}")
            return pd.DataFrame()

    def get_performance_trends(self):
        """Generate performance trend data"""
        try:
            df = self.db.get_performance_data()
            if df.empty:
                return pd.DataFrame()
            df['metric_date'] = pd.to_datetime(df['metric_date'], errors='coerce')
            trend = (
                df.groupby('metric_date')['overall_score']
                .mean()
                .reset_index()
                .rename(columns={'metric_date': 'date', 'overall_score': 'average_score'})
            )
            return trend
        except Exception as e:
            self.logger.error(f"Error generating performance trends: {e}")
            return pd.DataFrame()

    # -------------------------------------------------
    # Risk Analytics
    # -------------------------------------------------
    def get_risk_analysis(self):
        """Get risk distribution summary"""
        try:
            df = self.db.get_risk_data()
            if df.empty:
                return pd.DataFrame()

            if 'risk_level' not in df.columns and 'overall_risk' in df.columns:
                df['risk_level'] = np.select(
                    [df['overall_risk'] >= 70, df['overall_risk'] >= 40],
                    ['High', 'Medium'],
                    default='Low'
                )

            risk_summary = (
                df['risk_level']
                .value_counts()
                .reset_index()
                .rename(columns={'index': 'risk_level', 'risk_level': 'count'})
            )
            return risk_summary
        except Exception as e:
            self.logger.error(f"Error generating risk analysis: {e}")
            return pd.DataFrame()
           

    def get_vendor_risk_assessment(self):
        """Detailed risk assessment per vendor"""
        try:
            df = self.db.get_risk_data()
            if df.empty:
                return pd.DataFrame()

            expected_cols = ['vendor_id', 'risk_level', 'overall_risk', 'assessment_date']
            existing_cols = [c for c in expected_cols if c in df.columns]

            if not existing_cols:
                return pd.DataFrame(columns=expected_cols)

            return df[existing_cols]
        except Exception as e:
            self.logger.error(f"Error in get_vendor_risk_assessment: {e}")
            return pd.DataFrame(columns=['vendor_id', 'risk_level', 'overall_risk', 'assessment_date'])

    # -------------------------------------------------
    # Alerts & Notifications
    # -------------------------------------------------
    def get_recent_alerts(self):
        """Fetch simulated vendor alerts"""
        try:
            # You don't have an alerts table, so let's generate simulated alerts
            alerts = []
            vendors = self.db.get_vendors_with_performance()

            if vendors.empty:
                return []

            for _, row in vendors.head(5).iterrows():
                if row['performance_score'] < 60:
                    alerts.append({
                        "type": "High Risk Vendor",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "message": f"{row['name']} performance dropped below threshold."
                    })
            return alerts
        except Exception as e:
            self.logger.error(f"Error fetching recent alerts: {e}")
            return []
