from app import VendorDashboard


def test_risk_review_frame_has_business_columns():
    dashboard = VendorDashboard()
    review = dashboard._get_risk_review_frame()

    assert not review.empty
    for column in ["vendor_name", "priority_score", "risk_level", "overall_risk", "compliance_score"]:
        assert column in review.columns
