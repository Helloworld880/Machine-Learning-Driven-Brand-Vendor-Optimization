
# import pandas as pd
# import numpy as np
# import logging
# import os
# import pickle
# from datetime import datetime, timedelta

# from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor, IsolationForest
# from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import StandardScaler, LabelEncoder
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, mean_absolute_error
# from sklearn.pipeline import Pipeline

# logger = logging.getLogger(__name__)

# MODEL_DIR = "models"
# os.makedirs(MODEL_DIR, exist_ok=True)


# class MLEngine:
    
#     # Provides three ML capabilities:
#     # 1. Risk Scoring  – RandomForestClassifier predicts High / Medium / Low risk.
#     # 2. Churn Prediction – GradientBoostingRegressor predicts churn probability (0-1).
#     # 3. Performance Forecasting – Linear Regression 6-month forecast per vendor.
#     # 4. Anomaly Detection – IsolationForest flags unusual vendors.


#     def __init__(self, db):
#         self.db = db
#         self.risk_model: Pipeline | None = None
#         self.churn_model: Pipeline | None = None
#         self.forecast_model: Pipeline | None = None
#         self.anomaly_model: IsolationForest | None = None
#         self.label_enc = LabelEncoder()
#         self._load_or_train()

#     # ─────────────────────────────────────────────
#     # FEATURE ENGINEERING
#     # ─────────────────────────────────────────────
#     def _build_features(self) -> pd.DataFrame:
#         """Merge vendor, performance, financial and risk tables into feature matrix."""
#         vendors = self.db.get_vendors_with_performance()
#         fin = self.db.get_financial_data()
#         risk = self.db.get_risk_data()

#         if vendors.empty:
#             return pd.DataFrame()

#         df = vendors.copy()

#         # Financial aggregations per vendor
#         if not fin.empty and "vendor_id" in fin.columns:
#             fin_agg = fin.groupby("vendor_id").agg(
#                 total_spend=("total_spend", "sum"),
#                 total_savings=("cost_savings", "sum"),
#                 avg_payment_days=("payment_days", "mean"),
#             ).reset_index()
#             df = df.merge(fin_agg, on="vendor_id", how="left")

#         # Risk scores
#         if not risk.empty and "vendor_id" in risk.columns:
#             risk_agg = risk[["vendor_id", "financial_risk", "operational_risk",
#                               "compliance_risk", "overall_risk"]].drop_duplicates("vendor_id")
#             df = df.merge(risk_agg, on="vendor_id", how="left")

         
#         num_cols = ["avg_performance", "avg_on_time", "avg_defect_rate", "avg_quality",
#                     "contract_value", "rating", "total_spend", "total_savings",
#                     "avg_payment_days", "financial_risk", "operational_risk",
#                     "compliance_risk", "overall_risk"]
#         for col in num_cols:
#             if col in df.columns:
#                 df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
#             else:
#                 df[col] = 0.0

#         return df

#     # ─────────────────────────────────────────────
#     # TRAIN / LOAD
#     # ─────────────────────────────────────────────
#     def _load_or_train(self):
#         risk_path = os.path.join(MODEL_DIR, "risk_model.pkl")
#         churn_path = os.path.join(MODEL_DIR, "churn_model.pkl")

#         if os.path.exists(risk_path) and os.path.exists(churn_path):
#             try:
#                 with open(risk_path, "rb") as f:
#                     self.risk_model = pickle.load(f)
#                 with open(churn_path, "rb") as f:
#                     self.churn_model = pickle.load(f)
#                 logger.info("✅ ML models loaded from disk.")
#                 return
#             except Exception as e:
#                 logger.warning(f"Could not load models: {e}. Retraining.")
#         self._train_models()

#     def _train_models(self):
#         df = self._build_features()
#         if df.empty or len(df) < 5:
#             logger.warning("Not enough data to train models. Using synthetic augmentation.")
#             df = self._synthetic_augment(df)

#         feature_cols = ["avg_performance", "avg_on_time", "avg_defect_rate", "avg_quality",
#                         "contract_value", "rating", "total_spend", "total_savings",
#                         "avg_payment_days", "financial_risk", "operational_risk", "compliance_risk"]
#         feature_cols = [c for c in feature_cols if c in df.columns]
#         X = df[feature_cols].fillna(0)

#         # ── Risk Model (Classifier) ──────────────────
#         if "risk_level" in df.columns:
#             y_risk = df["risk_level"].fillna("Low")
#         else:
#             # derive from overall_risk
#             overall = df.get("overall_risk", pd.Series([30] * len(df)))
#             y_risk = pd.cut(overall, bins=[-1, 33, 66, 101],
#                             labels=["Low", "Medium", "High"])

#         self.risk_model = Pipeline([
#             ("scaler", StandardScaler()),
#             ("clf", RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")),
#         ])
#         try:
#             X_tr, X_te, y_tr, y_te = train_test_split(X, y_risk, test_size=0.2, random_state=42)
#             self.risk_model.fit(X_tr, y_tr)
#             acc = self.risk_model.score(X_te, y_te)
#             logger.info(f"Risk model accuracy: {acc:.2f}")
#         except Exception as e:
#             logger.warning(f"Risk model training issue: {e}. Fitting on full data.")
#             self.risk_model.fit(X, y_risk)

#         # ── Churn Model (Regressor → probability) ────
#         churn_score = 1 - (X["avg_performance"].clip(0, 100) / 100)
#         self.churn_model = Pipeline([
#             ("scaler", StandardScaler()),
#             ("reg", GradientBoostingRegressor(n_estimators=100, random_state=42)),
#         ])
#         try:
#             self.churn_model.fit(X, churn_score)
#         except Exception as e:
#             logger.warning(f"Churn model training issue: {e}")

#         # ── Anomaly Model ─────────────────────────────
#         self.anomaly_model = IsolationForest(contamination=0.1, random_state=42)
#         self.anomaly_model.fit(X)

#         # Save
#         try:
#             with open(os.path.join(MODEL_DIR, "risk_model.pkl"), "wb") as f:
#                 pickle.dump(self.risk_model, f)
#             with open(os.path.join(MODEL_DIR, "churn_model.pkl"), "wb") as f:
#                 pickle.dump(self.churn_model, f)
#             logger.info("✅ ML models trained and saved.")
#         except Exception as e:
#             logger.warning(f"Could not save models: {e}")

#     def _synthetic_augment(self, df: pd.DataFrame) -> pd.DataFrame:
#         """Create synthetic rows so models can train even with sparse DB data."""
#         np.random.seed(42)
#         rows = []
#         for _ in range(200):
#             rows.append({
#                 "avg_performance": np.random.uniform(40, 100),
#                 "avg_on_time": np.random.uniform(60, 100),
#                 "avg_defect_rate": np.random.uniform(0, 10),
#                 "avg_quality": np.random.uniform(50, 100),
#                 "contract_value": np.random.uniform(10000, 500000),
#                 "rating": np.random.uniform(1, 5),
#                 "total_spend": np.random.uniform(5000, 200000),
#                 "total_savings": np.random.uniform(0, 50000),
#                 "avg_payment_days": np.random.uniform(10, 90),
#                 "financial_risk": np.random.uniform(0, 100),
#                 "operational_risk": np.random.uniform(0, 100),
#                 "compliance_risk": np.random.uniform(0, 100),
#                 "risk_level": np.random.choice(["Low", "Medium", "High"]),
#             })
#         synth = pd.DataFrame(rows)
#         return pd.concat([df, synth], ignore_index=True) if not df.empty else synth

#     # ─────────────────────────────────────────────
#     # PREDICTION INTERFACES
#     # ─────────────────────────────────────────────
#     def predict_vendor_risks(self) -> pd.DataFrame:
#         """Return a DataFrame with ML-predicted risk levels for all vendors."""
#         df = self._build_features()
#         if df.empty or self.risk_model is None:
#             return pd.DataFrame()

#         feature_cols = ["avg_performance", "avg_on_time", "avg_defect_rate", "avg_quality",
#                         "contract_value", "rating", "total_spend", "total_savings",
#                         "avg_payment_days", "financial_risk", "operational_risk", "compliance_risk"]
#         feature_cols = [c for c in feature_cols if c in df.columns]
#         X = df[feature_cols].fillna(0)

#         try:
#             df["ml_risk_label"] = self.risk_model.predict(X)
#             proba = self.risk_model.predict_proba(X)
#             classes = self.risk_model.classes_
#             for i, cls in enumerate(classes):
#                 df[f"prob_{cls.lower()}"] = proba[:, i]
#         except Exception as e:
#             logger.error(f"Risk prediction error: {e}")
#             df["ml_risk_label"] = "Unknown"

#         return df[["vendor_id", "name", "category", "risk_level", "ml_risk_label",
#                    "avg_performance", "overall_risk"] +
#                   [c for c in df.columns if c.startswith("prob_")]].copy()

#     def predict_churn(self) -> pd.DataFrame:
#         """Return churn probability (0-1) per vendor."""
#         df = self._build_features()
#         if df.empty or self.churn_model is None:
#             return pd.DataFrame()

#         feature_cols = ["avg_performance", "avg_on_time", "avg_defect_rate", "avg_quality",
#                         "contract_value", "rating", "total_spend", "total_savings",
#                         "avg_payment_days", "financial_risk", "operational_risk", "compliance_risk"]
#         feature_cols = [c for c in feature_cols if c in df.columns]
#         X = df[feature_cols].fillna(0)

#         try:
#             df["churn_probability"] = self.churn_model.predict(X).clip(0, 1)
#             df["churn_risk"] = pd.cut(df["churn_probability"],
#                                       bins=[-0.01, 0.33, 0.66, 1.01],
#                                       labels=["Low", "Medium", "High"])
#         except Exception as e:
#             logger.error(f"Churn prediction error: {e}")
#             df["churn_probability"] = 0.0
#             df["churn_risk"] = "Unknown"

#         return df[["vendor_id", "name", "category", "churn_probability", "churn_risk"]].copy()

#     def forecast_performance(self, months_ahead: int = 6) -> pd.DataFrame:
#         """Simple linear trend forecast for each vendor over next N months."""
#         perf = self.db.get_performance_data()
#         if perf.empty:
#             return pd.DataFrame()

#         perf["metric_date"] = pd.to_datetime(perf["metric_date"], errors="coerce")
#         results = []

#         for vendor_id, group in perf.groupby("vendor_id"):
#             g = group.sort_values("metric_date").dropna(subset=["metric_date", "overall_score"])
#             if len(g) < 3:
#                 continue
#             g["t"] = (g["metric_date"] - g["metric_date"].min()).dt.days
#             X = g[["t"]].values
#             y = g["overall_score"].values
#             model = LinearRegression().fit(X, y)

#             last_t = int(g["t"].max())
#             for m in range(1, months_ahead + 1):
#                 future_t = last_t + m * 30
#                 forecast = float(model.predict([[future_t]])[0])
#                 forecast = max(0, min(100, forecast))
#                 results.append({
#                     "vendor_id": vendor_id,
#                     "vendor_name": g["vendor_name"].iloc[0] if "vendor_name" in g.columns else str(vendor_id),
#                     "forecast_date": (datetime.now() + timedelta(days=m * 30)).strftime("%Y-%m-%d"),
#                     "predicted_score": round(forecast, 2),
#                     "months_ahead": m,
#                 })

#         return pd.DataFrame(results)

#     def detect_anomalies(self) -> pd.DataFrame:
#         """Flag vendors whose metrics are unusually far from the norm."""
#         df = self._build_features()
#         if df.empty or self.anomaly_model is None:
#             return pd.DataFrame()

#         feature_cols = ["avg_performance", "avg_on_time", "avg_defect_rate", "avg_quality",
#                         "contract_value", "rating", "total_spend", "total_savings",
#                         "avg_payment_days", "financial_risk", "operational_risk", "compliance_risk"]
#         feature_cols = [c for c in feature_cols if c in df.columns]
#         X = df[feature_cols].fillna(0)

#         try:
#             preds = self.anomaly_model.predict(X)
#             scores = self.anomaly_model.score_samples(X)
#             df["anomaly"] = preds          # -1 = anomaly, 1 = normal
#             df["anomaly_score"] = scores   # more negative = more anomalous
#             df["is_anomaly"] = df["anomaly"] == -1
#         except Exception as e:
#             logger.error(f"Anomaly detection error: {e}")
#             df["is_anomaly"] = False

#         return df[["vendor_id", "name", "category", "is_anomaly",
#                    "anomaly_score", "avg_performance"]].copy()

#     def retrain(self):
#         """Force retrain and overwrite saved models."""
#         for fname in ["risk_model.pkl", "churn_model.pkl"]:
#             p = os.path.join(MODEL_DIR, fname)
#             if os.path.exists(p):
#                 os.remove(p)
#         self._train_models()
#         logger.info("✅ Models retrained successfully.")