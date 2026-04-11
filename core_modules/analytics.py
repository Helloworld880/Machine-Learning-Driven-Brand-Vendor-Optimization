# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import logging

# class AnalyticsEngine:
#     def __init__(self, db):
#         self.db = db
#         self.logger = logging.getLogger(__name__)

#     # -------------------------------------------------
#     # Vendor Performance Metrics
#     # -------------------------------------------------
#     def calculate_average_performance(self):
#         """Calculate average vendor performance score"""
#         try:
#             df = self.db.get_vendors_with_performance()
#             if df.empty:
#                 return 0.0
#             return df['performance_score'].mean()
#         except Exception as e:
#             self.logger.error(f"Error calculating average performance: {e}")
#             return 0.0

#     def get_high_risk_vendors_count(self):
#         """Count high-risk vendors"""
#         try:
#             df = self.db.get_risk_data()
#             if df.empty:
#                 return 0
#             if 'risk_level' in df.columns:
#                 return len(df[df['risk_level'].str.lower() == 'high'])
#             elif 'overall_risk' in df.columns:
#                 return len(df[df['overall_risk'] >= 70])  # threshold = 70%
#             return 0
#         except Exception as e:
#             self.logger.error(f"Error counting high-risk vendors: {e}")
#             return 0

#     def get_performance_distribution(self):
#         """Return distribution of performance scores"""
#         try:
#             df = self.db.get_vendors_with_performance()
#             if df.empty:
#                 return pd.DataFrame()
#             return df[['vendor_id', 'name', 'performance_score']]
#         except Exception as e:
#             self.logger.error(f"Error generating performance distribution: {e}")
#             return pd.DataFrame()

#     def get_performance_trends(self):
#         """Generate performance trend data"""
#         try:
#             df = self.db.get_performance_data()
#             if df.empty:
#                 return pd.DataFrame()
#             df['metric_date'] = pd.to_datetime(df['metric_date'], errors='coerce')
#             trend = (
#                 df.groupby('metric_date')['overall_score']
#                 .mean()
#                 .reset_index()
#                 .rename(columns={'metric_date': 'date', 'overall_score': 'average_score'})
#             )
#             return trend
#         except Exception as e:
#             self.logger.error(f"Error generating performance trends: {e}")
#             return pd.DataFrame()

#     # -------------------------------------------------
#     # Risk Analytics
#     # -------------------------------------------------
#     def get_risk_analysis(self):
#         """Get risk distribution summary"""
#         try:
#             df = self.db.get_risk_data()
#             if df.empty:
#                 return pd.DataFrame()

#             if 'risk_level' not in df.columns and 'overall_risk' in df.columns:
#                 df['risk_level'] = np.select(
#                     [df['overall_risk'] >= 70, df['overall_risk'] >= 40],
#                     ['High', 'Medium'],
#                     default='Low'
#                 )

#             risk_summary = (
#                 df['risk_level']
#                 .value_counts()
#                 .reset_index()
#                 .rename(columns={'index': 'risk_level', 'risk_level': 'count'})
#             )
#             return risk_summary
#         except Exception as e:
#             self.logger.error(f"Error generating risk analysis: {e}")
#             return pd.DataFrame()
           

#     def get_vendor_risk_assessment(self):
#         """Detailed risk assessment per vendor"""
#         try:
#             df = self.db.get_risk_data()
#             if df.empty:
#                 return pd.DataFrame()

#             expected_cols = ['vendor_id', 'risk_level', 'overall_risk', 'assessment_date']
#             existing_cols = [c for c in expected_cols if c in df.columns]

#             if not existing_cols:
#                 return pd.DataFrame(columns=expected_cols)

#             return df[existing_cols]
#         except Exception as e:
#             self.logger.error(f"Error in get_vendor_risk_assessment: {e}")
#             return pd.DataFrame(columns=['vendor_id', 'risk_level', 'overall_risk', 'assessment_date'])

#     # -------------------------------------------------
#     # Alerts & Notifications
#     # -------------------------------------------------
#     def get_recent_alerts(self):
#         """Fetch simulated vendor alerts"""
#         try:
#             # You don't have an alerts table, so let's generate simulated alerts
#             alerts = []
#             vendors = self.db.get_vendors_with_performance()

#             if vendors.empty:
#                 return []

#             for _, row in vendors.head(5).iterrows():
#                 if row['performance_score'] < 60:
#                     alerts.append({
#                         "type": "High Risk Vendor",
#                         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                         "message": f"{row['name']} performance dropped below threshold."
#                     })
#             return alerts
#         except Exception as e:
#             self.logger.error(f"Error fetching recent alerts: {e}")
#             return []


import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, db):
        self.db = db

    def get_kpi_summary(self) -> dict:
        """Return high-level KPIs for the overview dashboard."""
        try:
            vendors = self.db.get_vendors()
            perf = self.db.get_performance_data()
            risk = self.db.get_risk_data()
            fin = self.db.get_financial_summary()

            total_vendors = len(vendors)
            active_vendors = int((vendors["status"].str.lower() == "active").sum()) if not vendors.empty else 0
            avg_performance = round(float(perf["overall_score"].mean()), 1) if not perf.empty else 0.0
            high_risk_count = int((risk["risk_level"].str.lower() == "high").sum()) if not risk.empty else 0
            total_contract = float(vendors["contract_value"].sum()) if not vendors.empty else 0.0
            total_savings = float(fin["cost_savings"].sum()) if not fin.empty else 0.0

            return {
                "total_vendors": total_vendors,
                "active_vendors": active_vendors,
                "avg_performance": avg_performance,
                "high_risk_count": high_risk_count,
                "total_contract_value": total_contract,
                "total_cost_savings": total_savings,
            }
        except Exception as e:
            logger.error(f"KPI summary error: {e}")
            return {}

    def get_performance_trends(self) -> pd.DataFrame:
        try:
            return self.db.get_performance_trends()
        except Exception as e:
            logger.error(f"Performance trends error: {e}")
            return pd.DataFrame()

    def get_risk_distribution(self) -> pd.DataFrame:
        try:
            risk = self.db.get_risk_data()
            if risk.empty:
                return pd.DataFrame()
            return risk["risk_level"].value_counts().reset_index().rename(
                columns={"index": "risk_level", "risk_level": "count"})
        except Exception as e:
            logger.error(f"Risk distribution error: {e}")
            return pd.DataFrame()

    def get_recent_alerts(self) -> list:
        try:
            perf = self.db.get_vendors_with_performance()
            alerts = []
            if perf.empty:
                return alerts
            threshold = 70
            low_perf = perf[perf["avg_performance"].fillna(0) < threshold]
            for _, row in low_perf.head(5).iterrows():
                alerts.append({
                    "type": "⚠️ Low Performance",
                    "vendor": row.get("name", "Unknown"),
                    "message": f"Performance score {row.get('avg_performance', 0):.1f}% < {threshold}% threshold",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
            return alerts
        except Exception as e:
            logger.error(f"Alerts error: {e}")
            return []