from app import VendorDashboard


def test_data_health_panel_computes_counts():
    dashboard = VendorDashboard()
    rows = dashboard._data_health()

    assert rows, "expected data health rows"
    labels = {r.label for r in rows}
    assert {"Vendors", "Performance (latest)", "Financial", "Compliance", "Risk"}.issubset(labels)

    vendors = next(r for r in rows if r.label == "Vendors")
    assert vendors.rows > 0

