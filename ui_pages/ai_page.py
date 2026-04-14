from datetime import datetime
import json

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
                This workspace is powered by an LLM-backed assistant (with safe local fallbacks). Use it to identify
                priority vendors, generate leadership briefs, explain alerts, and ask your portfolio questions in one place.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Mode: `{ai_tools.AI_MODE}` | Last backend: `{ai_tools.LAST_AI_BACKEND}`")

    with st.expander("How the AI works", expanded=False):
        st.markdown(
            "- **auto (default)**: tries local Ollama first, then falls back to mock\n"
            "- **ollama**: local model only (no external calls)\n"
            "- **real**: Anthropic API (requires `ANTHROPIC_API_KEY`)\n"
            "- **mock**: rule-based demo mode (no external calls)\n"
        )

    perf_df, fin_df, perf_history, compliance, risk = dashboard._get_ai_dataframes()
    review = dashboard._get_risk_review_frame()

    if perf_df.empty or review.empty:
        st.warning("AI tools need vendor performance/risk data. Check sidebar → **Data Health** to confirm rows are present.")
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
                focus_df = pd.DataFrame(
                    {"risk_component": focus_cols, "score": [vendor_row.get(c, 0) for c in focus_cols]}
                )
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
        st.caption("Use concrete questions like “Which vendors are below 70% compliance?” or “Who has the highest cost variance?”")

        qcol1, qcol2, qcol3 = st.columns(3)
        if qcol1.button("Compliance below 70%", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which vendors have compliance below 70% and what are their scores?"
        if qcol2.button("Highest cost variance", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which vendor has the highest cost variance and what is the value?"
        if qcol3.button("Top 3 at-risk", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which are the top 3 at-risk vendors and why?"

        tcol1, tcol2 = st.columns([1, 1])
        vendor_scope = tcol1.selectbox("Scope", ["All vendors", "Single vendor"], key="ai_chat_scope")
        scoped_vendor = None
        if vendor_scope == "Single vendor":
            scoped_vendor = tcol2.selectbox(
                "Vendor",
                sorted(review["vendor_name"].dropna().unique().tolist()),
                key="ai_chat_vendor",
            )

        scoped_perf = perf_df
        scoped_fin = fin_df if not fin_df.empty else None
        if scoped_vendor:
            scoped_perf = perf_df[perf_df["vendor_name"] == scoped_vendor].copy()
            if scoped_fin is not None and "vendor_name" in scoped_fin.columns:
                scoped_fin = scoped_fin[scoped_fin["vendor_name"] == scoped_vendor].copy()
            with st.expander("Vendor context snapshot", expanded=False):
                st.dataframe(scoped_perf.head(8), use_container_width=True)
                if scoped_fin is not None and not scoped_fin.empty:
                    st.dataframe(scoped_fin.head(8), use_container_width=True)

        if st.button("Clear chat history", use_container_width=True):
            st.session_state.chat_history = []

        chat = VendorDataChat(scoped_perf, scoped_fin if scoped_fin is not None and not scoped_fin.empty else None, labels=["performance", "financial"])

        if st.session_state.get("__ai_suggested_prompt"):
            st.info(f"Suggested prompt: `{st.session_state['__ai_suggested_prompt']}` (paste into the input below)")

        streamlit_chat_widget(chat)

    with tabs[2]:
        st.subheader("Business-Ready Executive Brief")
        st.caption("Generates a leadership-ready summary using your current datasets.")
        brief_type = st.selectbox(
            "Brief focus",
            ["executive", "compliance", "financial", "risk"],
            key="hero_brief_type",
        )
        b1, b2 = st.columns([1, 1])
        if b1.button("Generate brief", use_container_width=True, type="primary"):
            generator = ReportSummaryGenerator()
            with st.spinner("Generating brief…"):
                summary = generator.generate(
                    vendor_df=perf_df,
                    period=datetime.now().strftime("%b %Y"),
                    financial_df=fin_df if not fin_df.empty else None,
                    summary_type=brief_type,
                )
            st.markdown(summary)
            st.caption(f"Backend used: `{ai_tools.LAST_AI_BACKEND}`")
            st.download_button(
                "Download brief as text",
                summary.encode("utf-8"),
                file_name=f"{brief_type}_brief.txt",
                mime="text/plain",
                use_container_width=True,
            )
        if b2.button("Generate + add top priorities", use_container_width=True):
            generator = ReportSummaryGenerator()
            with st.spinner("Generating brief…"):
                summary = generator.generate(
                    vendor_df=perf_df,
                    period=datetime.now().strftime("%b %Y"),
                    financial_df=fin_df if not fin_df.empty else None,
                    summary_type=brief_type,
                )
            st.markdown(summary)
            top_lines = "\n".join(
                f"- {row['vendor_name']}: priority score {row.get('priority_score', '—')}"
                for _, row in review.head(5).iterrows()
            )
            st.markdown("**Top priority vendors right now**\n" + top_lines)
            st.caption(f"Backend used: `{ai_tools.LAST_AI_BACKEND}`")

    with tabs[3]:
        st.subheader("Alert Studio")
        engine = SmartAlertEngine()
        alert_vendor = st.selectbox("Vendor", review["vendor_name"].tolist(), key="alert_vendor")
        vendor_row = review[review["vendor_name"] == alert_vendor].iloc[0]
        metric_choice = st.selectbox(
            "Metric",
            ["compliance score", "performance score", "overall risk"],
            key="alert_metric_choice",
        )

        threshold = 70.0 if metric_choice != "overall risk" else 60.0
        prev_val = None
        cur_val = None

        if metric_choice == "compliance score":
            cur_val = float(vendor_row.get("compliance_score", 0) or 0)
            prev_val = cur_val
            if compliance is not None and not compliance.empty and "vendor_name" in compliance.columns:
                v_hist = compliance[compliance["vendor_name"] == alert_vendor].copy()
                if not v_hist.empty:
                    date_col = "audit_date" if "audit_date" in v_hist.columns else None
                    score_col = "audit_score" if "audit_score" in v_hist.columns else ("compliance_score" if "compliance_score" in v_hist.columns else None)
                    if date_col and score_col:
                        v_hist[date_col] = pd.to_datetime(v_hist[date_col], errors="coerce")
                        v_hist = v_hist.sort_values(date_col)
                        if len(v_hist) >= 2:
                            prev_val = float(v_hist[score_col].iloc[-2] or prev_val)

        elif metric_choice == "performance score":
            cur_val = float(vendor_row.get("performance_score", 0) or 0)
            prev_val = cur_val
            if perf_history is not None and not perf_history.empty and "vendor_name" in perf_history.columns:
                v_hist = perf_history[perf_history["vendor_name"] == alert_vendor].copy()
                if not v_hist.empty and "metric_date" in v_hist.columns and "overall_score" in v_hist.columns:
                    v_hist["metric_date"] = pd.to_datetime(v_hist["metric_date"], errors="coerce")
                    v_hist = v_hist.sort_values("metric_date")
                    if len(v_hist) >= 2:
                        prev_val = float(v_hist["overall_score"].iloc[-2] or prev_val)

        else:  # overall risk
            cur_val = float(vendor_row.get("overall_risk", 0) or 0)
            prev_val = cur_val
            if risk is not None and not risk.empty and "vendor_name" in risk.columns:
                v_hist = risk[risk["vendor_name"] == alert_vendor].copy()
                if not v_hist.empty and "assessment_date" in v_hist.columns and "overall_risk" in v_hist.columns:
                    v_hist["assessment_date"] = pd.to_datetime(v_hist["assessment_date"], errors="coerce")
                    v_hist = v_hist.sort_values("assessment_date")
                    if len(v_hist) >= 2:
                        prev_val = float(v_hist["overall_risk"].iloc[-2] or prev_val)

        prev_val = float(prev_val if prev_val is not None else 0.0)
        cur_val = float(cur_val if cur_val is not None else 0.0)

        st.caption(f"Previous: {prev_val:.1f} → Current: {cur_val:.1f} | Threshold: {threshold:.1f}")
        if st.button("Explain alert", use_container_width=True):
            with st.spinner("Generating alert explanation…"):
                alert = engine.explain(
                    vendor_name=alert_vendor,
                    metric=metric_choice,
                    current_value=cur_val,
                    previous_value=prev_val,
                    threshold=threshold,
                )
            st.code(json.dumps(alert.to_dict(), indent=2))
            st.caption(f"Backend used: `{ai_tools.LAST_AI_BACKEND}`")
