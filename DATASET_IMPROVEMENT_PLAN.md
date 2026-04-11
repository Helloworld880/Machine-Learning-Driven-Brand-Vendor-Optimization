# Dataset Improvement Plan

This project already has a solid demo dataset, but the next quality jump will come from adding richer history, stronger business outcome labels, and a few missing source tables.

## Current strengths

- `vendors.csv`, `performance.csv`, `financial_metrics.csv`, and `brand.csv` are aligned on `vendor_id`
- Vendor names and categories are consistent across files
- The main analytics fields are complete and usable
- The current data is good enough for the Streamlit dashboard and AI summaries

## Main gaps

1. `brand.csv` only contains one snapshot per vendor, so trend analysis is weak.
2. `performance.csv` stops in 2024 while financial data spans a broader period.
3. There is no dedicated risk history CSV.
4. There is no dedicated compliance history CSV.
5. There are no clear ML target labels like churn, renewal, incident, or escalation.
6. Benchmark data is too small for deeper comparison features.

## Recommended new files

### `Data layer/risk_history.csv`
Purpose:
- Track vendor risk over time
- Power risk trends, alerting, and AI explanations

Suggested fields:
- `risk_id`
- `vendor_id`
- `vendor_name`
- `assessment_date`
- `financial_risk`
- `operational_risk`
- `compliance_risk`
- `geopolitical_risk`
- `cyber_risk`
- `overall_risk`
- `risk_level`
- `mitigation_status`
- `incident_flag`

### `Data layer/compliance_history.csv`
Purpose:
- Track audit outcomes and compliance movement over time
- Support compliance dashboards and alert explanations

Suggested fields:
- `compliance_id`
- `vendor_id`
- `vendor_name`
- `audit_date`
- `compliance_score`
- `compliance_status`
- `certifications`
- `major_findings`
- `minor_findings`
- `regulatory_breach_flag`
- `corrective_action_status`
- `next_audit_date`

### `Data layer/vendor_outcomes.csv`
Purpose:
- Add supervised ML labels and business outcomes
- Improve churn, renewal, and escalation modeling

Suggested fields:
- `outcome_id`
- `vendor_id`
- `vendor_name`
- `period`
- `contract_renewed`
- `renewal_term_months`
- `churned`
- `escalation_flag`
- `incident_count`
- `sla_breach_flag`
- `payment_dispute_flag`
- `relationship_health`

## Recommended upgrades to existing files

### `vendors.csv`
Add:
- `vendor_owner`
- `region`
- `criticality_tier`
- `contract_type`
- `preferred_vendor_flag`

### `performance.csv`
Add:
- 2025 monthly rows
- `late_deliveries`
- `open_issues`
- `repeat_issue_rate`
- `service_credit_flag`

### `financial_metrics.csv`
Add:
- `forecast_spend`
- `payment_delay_days`
- `penalty_cost`
- `currency`
- `spend_under_management`

### `brand.csv`
Add:
- multiple `assessment_date` values per vendor
- `pr_incident_flag`
- `sentiment_score`
- `brand_alignment_score`

### `industry_benchmarks.csv`
Add:
- more categories
- more KPIs like `avg_compliance_benchmark`, `avg_esg_benchmark`, `payment_days_target`

## Best order to improve

1. Extend `performance.csv` and `financial_metrics.csv` into 2025
2. Convert `brand.csv` into a time-series file
3. Add `risk_history.csv`
4. Add `compliance_history.csv`
5. Add `vendor_outcomes.csv`
6. Expand `industry_benchmarks.csv`

## Expected impact

- Better AI answers: high
- Better reports: high
- Better ML usefulness: very high
- Better dashboards: medium to high

## Practical target

If these upgrades are added, dataset quality can likely move from about `78%` to around `90%+` for this project.
