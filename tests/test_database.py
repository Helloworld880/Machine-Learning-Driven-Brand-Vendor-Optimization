from core_modules.database import DatabaseManager


def test_database_exposes_connected_history_datasets():
    db = DatabaseManager()
    risk_history = db.get_risk_history()
    compliance_history = db.get_compliance_history()
    outcomes = db.get_vendor_outcomes()

    assert len(risk_history) >= 98
    assert len(compliance_history) >= 98
    assert len(outcomes) >= 98
    assert "vendor_name" in risk_history.columns
    assert "relationship_health" in outcomes.columns
