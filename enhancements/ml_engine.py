import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split


class MLEngine:
    def __init__(self, db):
        self.db = db
        self.model = None

    def _latest_by(self, df: pd.DataFrame, group_col: str, sort_col: str) -> pd.DataFrame:
        if df.empty or group_col not in df.columns or sort_col not in df.columns:
            return pd.DataFrame()
        work = df.copy()
        work[sort_col] = pd.to_datetime(work[sort_col], errors="coerce")
        return work.sort_values(sort_col).drop_duplicates(group_col, keep="last")

    def _linear_trend(self, values) -> float:
        clean = pd.Series(values).dropna().astype(float)
        if len(clean) < 2:
            return 0.0
        x = np.arange(len(clean)).reshape(-1, 1)
        model = LinearRegression()
        model.fit(x, clean.values)
        return float(model.coef_[0])

    def _project_forward(self, values, steps_ahead: int = 3) -> float:
        clean = pd.Series(values).dropna().astype(float)
        if clean.empty:
            return 0.0
        if len(clean) < 2:
            return float(clean.iloc[-1])
        x = np.arange(len(clean)).reshape(-1, 1)
        model = LinearRegression()
        model.fit(x, clean.values)
        future_x = np.array([[len(clean) - 1 + steps_ahead]])
        return float(model.predict(future_x)[0])

    def _risk_label(self, score: float) -> str:
        if score >= 60:
            return "High"
        if score >= 35:
            return "Medium"
        return "Low"

    def _churn_label(self, probability: float) -> str:
        if probability >= 0.6:
            return "High"
        if probability >= 0.3:
            return "Medium"
        return "Low"

    def _rating_label(self, score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        return "D"

    def _feature_frame(self) -> pd.DataFrame:
        vendors = self.db.get_vendors_with_performance().copy()
        if vendors.empty:
            return pd.DataFrame()

        vendors = vendors.rename(columns={"name": "vendor_name"})
        for col in ["avg_performance", "avg_on_time", "avg_defect_rate", "avg_quality", "overall_risk"]:
            if col not in vendors.columns:
                vendors[col] = np.nan

        risk_history = self.db.get_risk_history().copy()
        compliance_history = self.db.get_compliance_history().copy()
        financial = self.db.get_financial_data().copy()
        outcomes = self.db.get_vendor_outcomes().copy()

        if not risk_history.empty:
            risk_history["assessment_date"] = pd.to_datetime(risk_history["assessment_date"], errors="coerce")
            risk_latest = self._latest_by(risk_history, "vendor_id", "assessment_date")
            risk_trends = (
                risk_history.sort_values("assessment_date")
                .groupby("vendor_id", as_index=False)
                .agg(
                    latest_risk=("overall_risk", "last"),
                    avg_financial_risk=("financial_risk", "mean"),
                    avg_operational_risk=("operational_risk", "mean"),
                    avg_compliance_risk=("compliance_risk", "mean"),
                    incident_count=("incident_flag", "sum"),
                )
            )
            risk_trends["risk_trend_slope"] = risk_history.groupby("vendor_id")["overall_risk"].apply(self._linear_trend).values
            vendors = vendors.merge(
                risk_latest[["vendor_id", "overall_risk", "risk_level", "mitigation_status"]],
                on="vendor_id",
                how="left",
                suffixes=("", "_latest"),
            )
            vendors = vendors.merge(risk_trends, on="vendor_id", how="left")

        if not compliance_history.empty:
            compliance_history["audit_date"] = pd.to_datetime(compliance_history["audit_date"], errors="coerce")
            comp_latest = self._latest_by(compliance_history, "vendor_id", "audit_date")
            comp_trends = (
                compliance_history.sort_values("audit_date")
                .groupby("vendor_id", as_index=False)
                .agg(
                    compliance_score=("audit_score", "last"),
                    avg_compliance_score=("audit_score", "mean"),
                    regulatory_breaches=("regulatory_breach_flag", "sum"),
                )
            )
            comp_trends["compliance_trend_slope"] = compliance_history.groupby("vendor_id")["audit_score"].apply(self._linear_trend).values
            vendors = vendors.merge(
                comp_latest[["vendor_id", "audit_score", "compliance_status", "corrective_action_status"]],
                on="vendor_id",
                how="left",
            )
            vendors = vendors.merge(comp_trends, on="vendor_id", how="left", suffixes=("", "_trend"))

        if not financial.empty:
            if "period" in financial.columns:
                financial["period_sort"] = financial["period"].astype(str)
            fin_latest = financial.sort_values("period_sort" if "period_sort" in financial.columns else "vendor_id").drop_duplicates("vendor_id", keep="last")
            fin_agg = (
                financial.groupby("vendor_id", as_index=False)
                .agg(
                    total_spend=("total_spend", "sum"),
                    total_savings=("cost_savings", "sum"),
                    avg_cost_variance=("cost_variance", "mean"),
                    avg_roi_score=("roi_score", "mean"),
                    avg_budget_utilization=("budget_utilization", "mean"),
                    overdue_invoices=("overdue_invoices", "sum"),
                )
            )
            fin_agg["cost_fluctuation"] = financial.groupby("vendor_id")["cost_variance"].std(ddof=0).values
            fin_agg["cost_trend_slope"] = financial.groupby("vendor_id")["cost_variance"].apply(self._linear_trend).values
            vendors = vendors.merge(
                fin_latest[["vendor_id", "cost_variance", "roi_score", "budget_utilization", "discount_availed"]],
                on="vendor_id",
                how="left",
            )
            vendors = vendors.merge(fin_agg, on="vendor_id", how="left", suffixes=("", "_agg"))

        if not outcomes.empty:
            outcomes = outcomes.sort_values("period")
            out_latest = outcomes.drop_duplicates("vendor_id", keep="last")
            out_agg = (
                outcomes.groupby("vendor_id", as_index=False)
                .agg(
                    renewals=("contract_renewed", "sum"),
                    churned=("churned", "max"),
                    escalations=("escalation_flag", "sum"),
                    incidents=("incident_count", "sum"),
                    sla_breaches=("sla_breach_flag", "sum"),
                    payment_disputes=("payment_dispute_flag", "sum"),
                )
            )
            vendors = vendors.merge(
                out_latest[["vendor_id", "relationship_health", "churned", "escalation_flag"]],
                on="vendor_id",
                how="left",
            )
            vendors = vendors.merge(out_agg, on="vendor_id", how="left", suffixes=("", "_agg"))

        numeric_cols = [
            "avg_performance",
            "avg_on_time",
            "avg_defect_rate",
            "avg_quality",
            "overall_risk",
            "latest_risk",
            "avg_financial_risk",
            "avg_operational_risk",
            "avg_compliance_risk",
            "risk_trend_slope",
            "audit_score",
            "compliance_score",
            "avg_compliance_score",
            "compliance_trend_slope",
            "cost_variance",
            "avg_cost_variance",
            "avg_roi_score",
            "avg_budget_utilization",
            "cost_fluctuation",
            "cost_trend_slope",
            "total_savings",
            "total_spend",
            "overdue_invoices",
            "contract_value",
            "renewals",
            "churned",
            "escalations",
            "incidents",
            "sla_breaches",
            "payment_disputes",
            "incident_count",
            "regulatory_breaches",
        ]
        for col in numeric_cols:
            if col not in vendors.columns:
                vendors[col] = 0.0
            vendors[col] = pd.to_numeric(vendors[col], errors="coerce").fillna(0.0)

        if "compliance_score" not in vendors.columns or (vendors["compliance_score"] == 0).all():
            vendors["compliance_score"] = vendors["audit_score"].where(vendors["audit_score"] > 0, vendors["avg_performance"])

        vendors["savings_rate"] = np.where(
            vendors["total_spend"] > 0,
            vendors["total_savings"] / vendors["total_spend"],
            0.0,
        )
        vendors["delivery_consistency"] = vendors["avg_on_time"]
        vendors["quality_consistency"] = vendors["avg_quality"]
        vendors["defect_penalty"] = vendors["avg_defect_rate"] * 4

        return vendors

    def _outlook_driver(self, performance_delta: float, risk_delta: float, cost_delta: float) -> str:
        drivers = {
            "Performance decline": abs(min(performance_delta, 0)),
            "Rising risk trend": max(risk_delta, 0),
            "Procurement cost pressure": max(cost_delta / 1000, 0),
        }
        return max(drivers, key=drivers.get)

    def train_model(self, df):
        features = ["on_time_pct", "defect_rate_pct", "quality_score"]
        target = "overall_score"
        X = df[features]
        y = df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        return self.model.score(X_test, y_test)

    def predict(self, data):
        if self.model is None:
            raise ValueError("Model not trained yet")
        return self.model.predict(data)

    def predict_vendor_risks(self):
        df = self._feature_frame()
        if df.empty:
            return pd.DataFrame()

        df["overall_risk"] = (
            (100 - df["avg_performance"]) * 0.35
            + (100 - df["avg_on_time"]) * 0.20
            + df["avg_defect_rate"] * 3.0
            + (100 - df["compliance_score"]) * 0.20
            + df["avg_cost_variance"].clip(lower=0) / 5000
            + df["avg_financial_risk"] * 0.10
            + df["risk_trend_slope"].clip(lower=0) * 2.5
        ).clip(0, 100)

        df["ml_risk_label"] = df["overall_risk"].apply(self._risk_label)
        df["prob_high"] = (df["overall_risk"] / 100).clip(0, 1)
        df["prob_medium"] = np.where(
            df["overall_risk"].between(35, 60),
            0.55,
            np.where(df["overall_risk"] < 35, 0.25, 0.30),
        )
        df["prob_low"] = (1 - df["prob_high"]).clip(0, 1) * 0.8
        return df

    def predict_churn(self):
        df = self._feature_frame()
        if df.empty:
            return pd.DataFrame()

        relationship_map = {"Strong": 0.05, "Stable": 0.15, "Watch": 0.35, "Fragile": 0.55}
        rel_penalty = df.get("relationship_health", pd.Series(["Stable"] * len(df))).map(relationship_map).fillna(0.2)
        df["churn_probability"] = (
            (100 - df["avg_performance"]) / 100 * 0.28
            + (100 - df["compliance_score"]) / 100 * 0.18
            + (df["overall_risk"] / 100) * 0.18
            + (df["escalations"] > 0).astype(float) * 0.12
            + (df["payment_disputes"] > 0).astype(float) * 0.10
            + (df["sla_breaches"] > 0).astype(float) * 0.08
            + rel_penalty * 0.30
        ).clip(0, 1)
        df["churn_risk"] = df["churn_probability"].apply(self._churn_label)
        return df

    def forecast_performance(self, months_ahead=6):
        perf = self.db.get_performance_data().copy()
        if perf.empty:
            return pd.DataFrame()

        perf["metric_date"] = pd.to_datetime(perf["metric_date"], errors="coerce")
        results = []
        for vendor in perf["vendor_name"].dropna().unique():
            vendor_df = perf[perf["vendor_name"] == vendor].sort_values("metric_date")
            if len(vendor_df) < 3:
                continue
            X = np.arange(len(vendor_df)).reshape(-1, 1)
            y = vendor_df["overall_score"].astype(float)
            model = LinearRegression()
            model.fit(X, y)
            future = np.arange(len(vendor_df), len(vendor_df) + months_ahead).reshape(-1, 1)
            preds = model.predict(future)
            future_dates = pd.date_range(vendor_df["metric_date"].max(), periods=months_ahead + 1, freq="M")[1:]

            for d, p in zip(future_dates, preds):
                results.append(
                    {
                        "vendor_name": vendor,
                        "forecast_date": d,
                        "predicted_score": float(np.clip(p, 0, 100)),
                    }
                )
        return pd.DataFrame(results)

    def forecast_vendor_outlook(self, periods_ahead=3):
        perf = self.db.get_performance_data().copy()
        risk = self.db.get_risk_history().copy()
        fin = self.db.get_financial_data().copy()
        base = self._feature_frame()
        if base.empty:
            return pd.DataFrame()

        results = []
        for _, vendor in base.iterrows():
            vendor_name = vendor["vendor_name"]
            vendor_id = vendor["vendor_id"]

            perf_values = perf[perf["vendor_id"] == vendor_id].sort_values("metric_date")["overall_score"] if not perf.empty else pd.Series(dtype=float)
            risk_values = risk[risk["vendor_id"] == vendor_id].sort_values("assessment_date")["overall_risk"] if not risk.empty else pd.Series(dtype=float)
            cost_values = fin[fin["vendor_id"] == vendor_id].sort_values("period")["cost_variance"] if not fin.empty else pd.Series(dtype=float)

            predicted_performance = np.clip(self._project_forward(perf_values, periods_ahead), 0, 100)
            predicted_risk = np.clip(self._project_forward(risk_values, periods_ahead), 0, 100)
            predicted_cost_variance = self._project_forward(cost_values, periods_ahead)

            performance_delta = predicted_performance - float(perf_values.dropna().iloc[-1]) if len(perf_values.dropna()) else 0.0
            risk_delta = predicted_risk - float(risk_values.dropna().iloc[-1]) if len(risk_values.dropna()) else 0.0
            cost_delta = predicted_cost_variance - float(cost_values.dropna().iloc[-1]) if len(cost_values.dropna()) else 0.0

            outlook = "Stable"
            if predicted_risk >= 60 or predicted_performance < 65 or cost_delta > 10000:
                outlook = "Needs Attention"
            if predicted_risk >= 75 or predicted_performance < 55:
                outlook = "Critical"
            if predicted_risk < 35 and predicted_performance >= 80 and cost_delta <= 0:
                outlook = "Positive"

            primary_driver = self._outlook_driver(performance_delta, risk_delta, cost_delta)
            recommended_action = (
                "Escalate vendor into weekly review and align procurement, operations, and compliance owners."
                if outlook == "Critical"
                else "Set a corrective action plan and review cost/risk movement in the next cycle."
                if outlook == "Needs Attention"
                else "Maintain monitoring cadence and preserve performance momentum."
            )

            results.append(
                {
                    "vendor_id": vendor_id,
                    "vendor_name": vendor_name,
                    "category": vendor.get("category"),
                    "current_performance": round(float(vendor.get("avg_performance", 0)), 2),
                    "predicted_performance": round(float(predicted_performance), 2),
                    "performance_delta": round(float(performance_delta), 2),
                    "current_risk": round(float(vendor.get("overall_risk", 0)), 2),
                    "predicted_risk": round(float(predicted_risk), 2),
                    "risk_delta": round(float(risk_delta), 2),
                    "current_cost_variance": round(float(vendor.get("cost_variance", 0)), 2),
                    "predicted_cost_variance": round(float(predicted_cost_variance), 2),
                    "cost_variance_delta": round(float(cost_delta), 2),
                    "procurement_cost_outlook": "Rising" if cost_delta > 0 else "Improving",
                    "vendor_outlook": outlook,
                    "predicted_risk_label": self._risk_label(predicted_risk),
                    "primary_driver": primary_driver,
                    "recommended_action": recommended_action,
                }
            )

        return pd.DataFrame(results).sort_values(["predicted_risk", "predicted_cost_variance"], ascending=[False, False])

    def auto_rate_vendors(self):
        df = self._feature_frame()
        if df.empty:
            return pd.DataFrame()

        df["delivery_component"] = df["delivery_consistency"] * 0.22
        df["quality_component"] = df["quality_consistency"] * 0.22
        df["compliance_component"] = df["compliance_score"] * 0.20
        df["performance_component"] = df["avg_performance"] * 0.18
        df["savings_component"] = (df["savings_rate"] * 100).clip(0, 100) * 0.10
        df["risk_component"] = (100 - df["overall_risk"]).clip(0, 100) * 0.08
        df["defect_penalty_component"] = df["defect_penalty"] * 0.05

        df["rating_score"] = (
            df["delivery_component"]
            + df["quality_component"]
            + df["compliance_component"]
            + df["performance_component"]
            + df["savings_component"]
            + df["risk_component"]
            - df["defect_penalty_component"]
        ).clip(0, 100)

        df["vendor_rating"] = df["rating_score"].apply(self._rating_label)
        df["star_rating"] = (df["rating_score"] / 20).clip(1, 5).round(1)
        df["improvement_gap_to_a"] = (85 - df["rating_score"]).clip(lower=0).round(2)
        df["rating_summary"] = np.select(
            [
                df["vendor_rating"] == "A",
                df["vendor_rating"] == "B",
                df["vendor_rating"] == "C",
            ],
            [
                "High-performing strategic vendor",
                "Reliable vendor with manageable improvement areas",
                "Acceptable vendor that needs active performance management",
            ],
            default="Underperforming vendor requiring intervention",
        )
        return df.sort_values("rating_score", ascending=False)

    def simulate_vendor_rating(
        self,
        delivery_consistency: float,
        quality_score: float,
        compliance_score: float,
        performance_score: float,
        savings_rate_pct: float,
        overall_risk: float,
        defect_rate: float,
    ) -> dict:
        savings_component = np.clip(savings_rate_pct, 0, 100) * 0.10
        score = (
            delivery_consistency * 0.22
            + quality_score * 0.22
            + compliance_score * 0.20
            + performance_score * 0.18
            + savings_component
            + (100 - overall_risk) * 0.08
            - (defect_rate * 4) * 0.05
        )
        score = float(np.clip(score, 0, 100))
        return {
            "rating_score": round(score, 2),
            "vendor_rating": self._rating_label(score),
            "star_rating": round(float(np.clip(score / 20, 1, 5)), 1),
        }

    def detect_anomalies(self):
        df = self._feature_frame()
        if df.empty:
            return pd.DataFrame()
        features = df[["avg_performance", "avg_on_time", "avg_quality", "avg_defect_rate", "compliance_score", "overall_risk"]]
        model = IsolationForest(contamination=0.1, random_state=42)
        anomaly_flags = model.fit_predict(features)
        decision_scores = model.decision_function(features)
        df["anomaly_score"] = decision_scores
        df["is_anomaly"] = anomaly_flags == -1
        return df

    def retrain(self):
        perf = self.db.get_performance_data()
        if perf.empty:
            return
        self.train_model(perf)
