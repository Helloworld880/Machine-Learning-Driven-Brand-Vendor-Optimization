from enhancements.ml_engine import MLEngine
from core_modules.database import DatabaseManager


def test_predictive_outlook_returns_expected_columns():
    ml = MLEngine(DatabaseManager())
    outlook = ml.forecast_vendor_outlook(periods_ahead=3)
    assert not outlook.empty
    for column in [
        "vendor_name",
        "predicted_performance",
        "predicted_risk",
        "predicted_cost_variance",
        "vendor_outlook",
        "primary_driver",
        "recommended_action",
    ]:
        assert column in outlook.columns


def test_auto_rate_vendors_returns_rating_fields():
    ml = MLEngine(DatabaseManager())
    ratings = ml.auto_rate_vendors()
    assert not ratings.empty
    for column in [
        "vendor_name",
        "rating_score",
        "vendor_rating",
        "star_rating",
        "rating_summary",
        "delivery_component",
        "improvement_gap_to_a",
    ]:
        assert column in ratings.columns


def test_rating_simulator_returns_grade():
    ml = MLEngine(DatabaseManager())
    result = ml.simulate_vendor_rating(90, 88, 92, 91, 12, 25, 2)
    assert result["vendor_rating"] in {"A", "B", "C", "D"}
    assert result["rating_score"] >= 0
