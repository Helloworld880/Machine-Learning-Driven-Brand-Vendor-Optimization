import pandas as pd

import ai_integration
from ai_integration import VendorDataChat


def test_mock_ai_answers_data_question():
    ai_integration.AI_MODE = "mock"
    perf = pd.DataFrame(
        [
            {"vendor_name": "Vendor A", "compliance_score": 82, "on_time_delivery": 91, "quality_score": 88},
            {"vendor_name": "Vendor B", "compliance_score": 61, "on_time_delivery": 77, "quality_score": 71},
        ]
    )
    fin = pd.DataFrame(
        [
            {"vendor_name": "Vendor A", "contract_value": 100000, "actual_cost": 110000},
            {"vendor_name": "Vendor B", "contract_value": 100000, "actual_cost": 135000},
        ]
    )
    chat = VendorDataChat(perf, fin, labels=["performance", "financial"])
    answer = chat.ask("Which vendors have compliance below 70%?")
    assert "Vendor B" in answer
    assert ai_integration.LAST_AI_BACKEND == "mock"
