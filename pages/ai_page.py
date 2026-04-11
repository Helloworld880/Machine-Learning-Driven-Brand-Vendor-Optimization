from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import ai_integration as ai_tools
from ai_integration import (
    ReportSummaryGenerator,
    SmartAlertEngine,
    VendorDataChat,
    streamlit_chat_widget,
)


def _format_pct(val):
    try:
        return f"{float(val):.1f}%"
    except Exception:
        return "—"


def _fmt_currency(val):
    try:
        amount = float(val or 0)
    except Exception:
        amount = 0.0
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:,.0f}"


def render_ai_workspace(dashboard):
    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-kicker">AI Command Center</div>
            <div class="hero-title">Turn vendor risk signals into executive-ready actions</div>
            <p class="hero-copy">
                This workspace is the product hero for the MVP: identify priority vendors, generate leadership briefs,
                explain alerts, and ask your portfolio questions in one place.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Mode: `{ai_tools.AI_MODE}` | Last backend: `{ai_tools.LAST_AI_BACKEND}`")

    perf_df, fin_df, perf_history, compliance, risk = dashboard._get_ai_dataframes()
    review = dashboard._get_risk_review_frame()

    if perf_df.empty or review.empty:
        st.warning("AI tools need vendor performance data, but none is available right now.")
        return

    top3 = review.head(3)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Priority Vendors", len(review))
    k2.metric("High Risk Now", int((review["risk_level"] == "High").sum()))
    k3.metric("Below 70 Compliance", int((review["compliance_score"].fillna(100) < 70).sum()))
    k4.metric("Average Priority Score", f"{review['priority_score'].mean():.1f}")

    st.divider()
    left, right = st.columns([1.1, 1.4])
    with left:
        st.subheader("Top Review Queue")
        st.caption("These vendors need the fastest attention based on risk, performance, and compliance.")
        for _, row in top3.iterrows():
            dashboard._render_priority_card(row)

    with right:
        st.subheader("Executive Takeaways")
        generator = ReportSummaryGenerator()
        with st.spinner("Refreshing executive brief..."):
            exec_summary = generator.generate(
                vendor_df=perf_df,
                period=datetime.now().strftime("%b %Y"),
                financial_df=fin_df if not fin_df.empty else None,
                summary_type="executive",
            )
        st.markdown(exec_summary)
        if not top3.empty:
            action_lines = [
                f"Prioritize {row['vendor_name']} for follow-up due to a priority score of {row['priority_score']}."
                for _, row in top3.iterrows()
            ]
            st.info("\n".join(action_lines))
        st.caption(f"Backend used: `{ai_tools.LAST_AI_BACKEND}`")

    tabs = st.tabs(["Risk Review", "Ask Data", "Executive Brief", "Alert Studio"])

    with tabs[0]:
        st.subheader("Risk Review Workflow")
        vendor_options = review["vendor_name"].tolist()
        selected_vendor = st.selectbox("Select priority vendor", vendor_options, key="hero_risk_vendor")
        vendor_row = review[review["vendor_name"] == selected_vendor].iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Risk", _format_pct(vendor_row.get("overall_risk")))
        c2.metric("Performance", _format_pct(vendor_row.get("performance_score")))
        c3.metric("Compliance", _format_pct(vendor_row.get("compliance_score")))
        c4.metric("Cost Variance", _fmt_currency(vendor_row.get("cost_variance", 0) or 0))

        r1, r2 = st.columns([1.2, 1])
        with r1:
            focus_cols = [c for c in ["financial_risk", "operational_risk", "compliance_risk"] if c in review.columns]
            if focus_cols:
                focus_df = pd.DataFrame({"risk_component": focus_cols, "score": [vendor_row.get(c, 0) for c in focus_cols]})
                fig = px.bar(
                    focus_df,
                    x="risk_component",
                    y="score",
                    color="score",
                    color_continuous_scale="Reds",
                    title=f"{selected_vendor} risk component view",
                )
                st.plotly_chart(fig, use_container_width=True)

            if not perf_history.empty and "vendor_name" in perf_history.columns:
                v_hist = perf_history[perf_history["vendor_name"] == selected_vendor].sort_values("metric_date")
                if not v_hist.empty:
                    fig = px.line(
                        v_hist,
                        x="metric_date",
                        y="overall_score",
                        markers=True,
                        title=f"{selected_vendor} performance trend",
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with r2:
            st.markdown("**Action checklist**")
            checklist = [
                "Confirm the vendor owner and next checkpoint date.",
                "Review contract exposure and latest performance drift.",
                "Capture the current mitigation status in leadership notes.",
                "Decide whether this vendor stays in weekly review or moves to escalation.",
            ]
            for line in checklist:
                st.markdown(f"- {line}")

            st.markdown("**Leadership summary**")
            st.markdown(
                dashboard._risk_leadership_note(
                    vendor_row,
                    vendor_row.get("overall_risk", 0) - vendor_row.get("priority_score", 0),
                )
            )

    with tabs[1]:
        st.subheader("Ask Your Vendor Data")
        streamlit_chat_widget(perf_df, fin_df if not fin_df.empty else None)

    with tabs[2]:
        st.subheader("Business-Ready Executive Brief")
        brief_type = st.selectbox(
            "Brief focus",
            ["executive", "compliance", "financial", "risk"],
            key="hero_brief_type",
        )
        if st.button("Generate executive brief", use_container_width=True, type="primary"):
            generator = ReportSummaryGenerator()
            summary = generator.generate(
                vendor_df=perf_df,
                period=datetime.now().strftime("%b %Y"),
                financial_df=fin_df if not fin_df.empty else None,
                summary_type=brief_type,
            )
            st.markdown(summary)
            st.download_button(
                "Download brief as text",
                summary.encode("utf-8"),
                file_name=f"{brief_type}_brief.txt",
                mime="text/plain",
            )

    with tabs[3]:
        st.subheader("Alert Studio")
        engine = SmartAlertEngine()
        alert_vendor = st.selectbox("Vendor", review["vendor_name"].tolist(), key="alert_vendor")
        vendor_row = review[review["vendor_name"] == alert_vendor].iloc[0]
        previous_value = max(float(vendor_row.get("compliance_score", 0) or 0) + 8, 1)
        current_value = float(vendor_row.get("compliance_score", 0) or 0)
        if st.button("Explain compliance drop alert", use_container_width=True):
            explanation = engine.generate_alert_explanation(
                vendor_name=alert_vendor,
                metric="compliance score",
                previous_value=previous_value,
                current_value=current_value,
                threshold=70,
            )
            st.code(explanation)
