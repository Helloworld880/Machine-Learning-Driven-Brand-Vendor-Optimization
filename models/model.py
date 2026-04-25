import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


logger = logging.getLogger(__name__)


class VendorRiskModel:
    def __init__(self, model_path: str = "models/vendor_risk_model.joblib") -> None:
        self.model = RandomForestClassifier(n_estimators=150, random_state=42)
        self.is_fitted = False
        self.model_path = Path(model_path)
        self.feature_columns = [
            "delivery_rate",
            "quality_score",
            "cost_efficiency",
            "on_time_rate",
            "cost_variance",
            "reliability",
            "performance_score",
        ]
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    def train(self, frame: pd.DataFrame) -> None:
        if frame.empty:
            raise ValueError("Training data is empty.")

        train_frame = frame.copy()
        if "risk_label" not in train_frame.columns:
            train_frame["risk_label"] = np.where(train_frame["performance_score"] >= 70, "good", "risky")

        x = train_frame[self.feature_columns].fillna(0)
        y = train_frame["risk_label"]
        self.model.fit(x, y)
        self.is_fitted = True
        joblib.dump(self.model, self.model_path)
        logger.info("VendorRiskModel trained on %s records", len(train_frame))

    def load(self) -> None:
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
            self.is_fitted = True
            logger.info("VendorRiskModel loaded from %s", self.model_path)

    def predict_risk(self, frame: pd.DataFrame) -> pd.Series:
        if not self.is_fitted:
            self.load()
        if not self.is_fitted:
            self.train(frame)
        x = frame[self.feature_columns].fillna(0)
        return pd.Series(self.model.predict(x), index=frame.index, name="risk_prediction")
