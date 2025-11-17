import pandas as pd
from datetime import datetime

class FinancialAnalytics:
    def __init__(self, db_manager):
        self.db = db_manager

    def calculate_total_cost_savings(self):
        """Calculate total cost savings from all categories."""
        df = self.db.get_cost_savings()
        if df.empty:
            return 0
        return float(df["cost_savings"].sum())

    def get_cost_savings_breakdown(self):
        """Get cost savings by category and attach vendor performance info if available."""
        try:
            savings = self.db.get_cost_savings()
            vendors_data = self.db.get_vendors_with_performance()

            if savings.empty:
                return pd.DataFrame(columns=["category", "cost_savings"])

            # Clean data
            savings["category"] = savings["category"].fillna("Uncategorized")
            savings["cost_savings"] = savings["cost_savings"].fillna(0)

            # Optionally merge vendor performance
            if not vendors_data.empty:
                vendors_data = vendors_data[["vendor_id", "name", "performance_score", "total_sales"]]
                vendors_data.rename(columns={"name": "vendor_name"}, inplace=True)
                # Can be merged or kept separate depending on use
                # Example merge if needed:
                # savings = savings.merge(vendors_data, how="left", left_on="category", right_on="vendor_name")

            return savings
        except Exception as e:
            print(f"[ERROR] in get_cost_savings_breakdown: {e}")
            return pd.DataFrame(columns=["category", "cost_savings"])
