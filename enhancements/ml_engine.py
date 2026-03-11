import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split


class MLEngine:

    def __init__(self, db):
        self.db = db
        self.model = None

    # ─────────────────────────────
    # Train ML model
    # ─────────────────────────────
    def train_model(self, df):

        features = [
            "on_time_pct",
            "defect_rate_pct",
            "quality_score"
        ]

        target = "overall_score"

        X = df[features]
        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )

        self.model.fit(X_train, y_train)

        score = self.model.score(X_test, y_test)

        return score

    # ─────────────────────────────
    # Predict vendor performance
    # ─────────────────────────────
    def predict(self, data):

        if self.model is None:
            raise ValueError("Model not trained yet")

        return self.model.predict(data)

    # ─────────────────────────────
    # Vendor Risk Prediction
    # ─────────────────────────────
    def predict_vendor_risks(self):

        df = self.db.get_vendors_with_performance()

        if df.empty:
            return pd.DataFrame()

        df["overall_risk"] = (
            (100 - df["avg_performance"]) * 0.5 +
            df["avg_defect_rate"] * 5 +
            (100 - df["avg_on_time"]) * 0.3
        )

        def label(score):
            if score > 60:
                return "High"
            elif score > 35:
                return "Medium"
            else:
                return "Low"

        df["ml_risk_label"] = df["overall_risk"].apply(label)

        return df

    # ─────────────────────────────
    # Churn Prediction
    # ─────────────────────────────
    def predict_churn(self):

        df = self.db.get_vendors_with_performance()

        if df.empty:
            return pd.DataFrame()

        df["churn_probability"] = (100 - df["avg_performance"]) / 100

        df["churn_risk"] = df["churn_probability"].apply(
            lambda x: "High" if x > 0.6 else "Medium" if x > 0.3 else "Low"
        )

        return df

    # ─────────────────────────────
    # Performance Forecast
    # ─────────────────────────────
    def forecast_performance(self, months_ahead=6):

        perf = self.db.get_performance_data()

        if perf.empty:
            return pd.DataFrame()

        perf["metric_date"] = pd.to_datetime(perf["metric_date"])

        results = []

        for vendor in perf["vendor_name"].unique():

            vendor_df = perf[perf["vendor_name"] == vendor].sort_values("metric_date")

            if len(vendor_df) < 3:
                continue

            X = np.arange(len(vendor_df)).reshape(-1, 1)
            y = vendor_df["overall_score"]

            model = LinearRegression()
            model.fit(X, y)

            future = np.arange(len(vendor_df), len(vendor_df) + months_ahead).reshape(-1, 1)
            preds = model.predict(future)

            future_dates = pd.date_range(
                vendor_df["metric_date"].max(),
                periods=months_ahead + 1,
                freq="M"
            )[1:]

            for d, p in zip(future_dates, preds):

                results.append({
                    "vendor_name": vendor,
                    "forecast_date": d,
                    "predicted_score": p
                })

        return pd.DataFrame(results)

    # ─────────────────────────────
    # Anomaly Detection
    # ─────────────────────────────
    def detect_anomalies(self):

        df = self.db.get_vendors_with_performance()

        if df.empty:
            return pd.DataFrame()

        features = df[
            ["avg_performance", "avg_on_time", "avg_quality", "avg_defect_rate"]
        ]

        model = IsolationForest(contamination=0.1)

        df["anomaly_score"] = model.fit_predict(features)

        df["is_anomaly"] = df["anomaly_score"] == -1

        return df

    # ─────────────────────────────
    # Retrain models
    # ─────────────────────────────
    def retrain(self):

        perf = self.db.get_performance_data()

        if perf.empty:
            return

        self.train_model(perf)