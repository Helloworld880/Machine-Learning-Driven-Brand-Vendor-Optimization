import numpy as np
import pandas as pd
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _PLOTLY_AVAILABLE = True
    _PLOTLY_IMPORT_ERROR = None
except ImportError as e:
    px = None
    go = None
    make_subplots = None
    _PLOTLY_AVAILABLE = False
    _PLOTLY_IMPORT_ERROR = e
import streamlit as st


def _format_pct(val):
    try:
        return f"{float(val):.1f}%"
    except Exception:
        return "—"


def render_risk_management(dashboard):
    if not _PLOTLY_AVAILABLE:
        st.error("Plotly is not available in the current deployment, so the risk charts cannot load.")
        if _PLOTLY_IMPORT_ERROR is not None:
            st.caption(f"Import error: {_PLOTLY_IMPORT_ERROR}")
        return
    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-kicker">Risk Review Hub</div>
            <div class="hero-title">Prioritize the vendors that need action now</div>
            <p class="hero-copy">
                Review portfolio risk by severity, investigate component-level drivers, and track trend movement
                before issues turn into leadership escalations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    risk = pd.DataFrame(dashboard.db.get_risk_data())
    risk_history = pd.DataFrame(dashboard.db.get_risk_history())
    outcomes = pd.DataFrame(dashboard.db.get_vendor_outcomes())
    if risk.empty:
        st.warning("No risk data found. Check sidebar → **Data Health** to see whether `risk_history.csv` is missing/empty.")
        return

    risk = risk.copy()
    if "assessment_date" in risk.columns:
        risk["assessment_date"] = pd.to_datetime(risk["assessment_date"], errors="coerce")
    if not risk_history.empty and "assessment_date" in risk_history.columns:
        risk_history["assessment_date"] = pd.to_datetime(risk_history["assessment_date"], errors="coerce")
    if not outcomes.empty and "period" in outcomes.columns:
        outcomes = outcomes.sort_values("period")

    risk["incident_flag"] = pd.to_numeric(risk.get("incident_flag", 0), errors="coerce").fillna(0).astype(int)
    risk["review_priority"] = (
        risk["overall_risk"].fillna(0) * 0.55
        + risk["financial_risk"].fillna(0) * 0.20
        + risk["operational_risk"].fillna(0) * 0.15
        + risk["compliance_risk"].fillna(0) * 0.10
    ).round(1)

    if not risk_history.empty:
        history_sorted = risk_history.sort_values(["vendor_name", "assessment_date"])
        history_sorted["prior_overall_risk"] = history_sorted.groupby("vendor_name")["overall_risk"].shift(1)
        latest_history = history_sorted.drop_duplicates("vendor_name", keep="last").copy()
        latest_history["risk_delta"] = latest_history["overall_risk"] - latest_history["prior_overall_risk"]
        risk = risk.merge(latest_history[["vendor_name", "risk_delta"]], on="vendor_name", how="left")
    else:
        risk["risk_delta"] = np.nan

    filt1, filt2, filt3 = st.columns(3)
    categories = ["All"] + sorted([str(x) for x in risk["category"].dropna().unique().tolist()])
    levels = ["All"] + sorted([str(x) for x in risk["risk_level"].dropna().unique().tolist()])
    mitigations = ["All"] + sorted([str(x) for x in risk["mitigation_status"].dropna().unique().tolist()])
    selected_category = filt1.selectbox("Category", categories, key="risk_category_filter")
    selected_level = filt2.selectbox("Risk level", levels, key="risk_level_filter")
    selected_mitigation = filt3.selectbox("Mitigation status", mitigations, key="risk_mitigation_filter")

    filtered = risk.copy()
    if selected_category != "All":
        filtered = filtered[filtered["category"] == selected_category]
    if selected_level != "All":
        filtered = filtered[filtered["risk_level"] == selected_level]
    if selected_mitigation != "All":
        filtered = filtered[filtered["mitigation_status"] == selected_mitigation]

    filtered = filtered.sort_values(["review_priority", "overall_risk"], ascending=False)
    if filtered.empty:
        st.info("No vendors match the current filters.")
        return

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Vendors", len(filtered))
    k2.metric("High Risk", int((filtered["risk_level"] == "High").sum()))
    k3.metric("Immediate Review", int((filtered["review_priority"] >= 45).sum()))
    k4.metric("Avg Overall Risk", f"{filtered['overall_risk'].mean():.1f}%")
    k5.metric("Flagged Incidents", int(filtered["incident_flag"].sum()))

    st.divider()

    left, right = st.columns([1.05, 1.45])
    with left:
        st.subheader("Priority Queue")
        st.caption("Start with the vendors most likely to need intervention.")
        for _, row in filtered.head(6).iterrows():
            dashboard._render_priority_card(
                pd.Series(
                    {
                        "vendor_name": row.get("vendor_name"),
                        "risk_level": row.get("risk_level"),
                        "compliance_status": row.get("mitigation_status", "Monitoring"),
                        "priority_score": row.get("review_priority"),
                        "performance_score": 100 - row.get("operational_risk", 0),
                        "compliance_score": 100 - row.get("compliance_risk", 0),
                        "overall_risk": row.get("overall_risk"),
                    }
                )
            )

        review_cut = filtered.head(10)
        st.markdown(
            f"""
            <div class="insight-box">
                <div class="insight-title">Team focus this week</div>
                <div>{len(review_cut)} vendors sit at the top of the queue. Start with <strong>{review_cut.iloc[0]['vendor_name']}</strong>,
                then work downward by priority score to keep reviews consistent.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        export_cols = [
            c
            for c in [
                "vendor_name",
                "review_priority",
                "risk_level",
                "overall_risk",
                "financial_risk",
                "operational_risk",
                "compliance_risk",
                "mitigation_status",
                "incident_flag",
                "risk_delta",
            ]
            if c in filtered.columns
        ]
        st.download_button(
            "Download risk review queue",
            filtered[export_cols].to_csv(index=False).encode(),
            "risk_review_queue.csv",
            "text/csv",
        )

    with right:
        st.subheader("Portfolio Risk Snapshot")
        r1, r2 = st.columns(2)
        with r1:
            fig = px.pie(
                filtered,
                names="risk_level",
                color="risk_level",
                color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                hole=0.55,
                title="Current risk mix",
            )
            st.plotly_chart(fig, use_container_width=True)
        with r2:
            fig = px.scatter(
                filtered,
                x="financial_risk",
                y="operational_risk",
                color="risk_level",
                size="overall_risk",
                hover_name="vendor_name",
                color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                title="Financial vs operational exposure",
                labels={"financial_risk": "Financial Risk (%)", "operational_risk": "Operational Risk (%)"},
            )
            st.plotly_chart(fig, use_container_width=True)

        category_rollup = (
            filtered.groupby("category", dropna=False)
            .agg(avg_risk=("overall_risk", "mean"), vendors=("vendor_name", "count"))
            .reset_index()
            .sort_values("avg_risk", ascending=False)
        )
        if not category_rollup.empty:
            fig = px.bar(
                category_rollup,
                x="category",
                y="avg_risk",
                color="vendors",
                color_continuous_scale="Blues",
                title="Average overall risk by category",
                labels={"avg_risk": "Average risk (%)", "vendors": "Vendor count"},
            )
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Vendor Drill-Down")
    vendor_options = filtered["vendor_name"].dropna().tolist()
    selected_vendor = st.selectbox("Select vendor for review", vendor_options, key="risk_review_vendor")
    selected = filtered[filtered["vendor_name"] == selected_vendor].iloc[0]
    vendor_history = risk_history[risk_history["vendor_name"] == selected_vendor].sort_values("assessment_date")
    latest_outcome = pd.DataFrame()
    if not outcomes.empty:
        latest_outcome = outcomes[outcomes["vendor_name"] == selected_vendor].sort_values("period", ascending=False).head(1)
    trend_delta = selected.get("risk_delta")

    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Overall", _format_pct(selected.get("overall_risk")))
    d2.metric("Financial", _format_pct(selected.get("financial_risk")))
    d3.metric("Operational", _format_pct(selected.get("operational_risk")))
    d4.metric("Compliance", _format_pct(selected.get("compliance_risk")))
    d5.metric("Mitigation", str(selected.get("mitigation_status", "—")))

    st.markdown(
        f"""
        <div class="insight-box">
            <div class="insight-title">Leadership note</div>
            <div>{dashboard._risk_leadership_note(selected, trend_delta, latest_outcome)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_col, notes_col = st.columns([1.2, 1])
    with chart_col:
        comp_df = pd.DataFrame(
            {
                "component": ["financial_risk", "operational_risk", "compliance_risk", "geopolitical_risk", "cyber_risk"],
                "score": [
                    selected.get("financial_risk", 0),
                    selected.get("operational_risk", 0),
                    selected.get("compliance_risk", 0),
                    selected.get("geopolitical_risk", 0),
                    selected.get("cyber_risk", 0),
                ],
            }
        )
        fig = px.bar(
            comp_df,
            x="component",
            y="score",
            color="score",
            color_continuous_scale="Reds",
            title=f"{selected_vendor} risk component breakdown",
        )
        fig.update_xaxes(tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

        if not vendor_history.empty:
            fig = px.line(
                vendor_history,
                x="assessment_date",
                y=["overall_risk", "financial_risk", "operational_risk", "compliance_risk"],
                markers=True,
                title=f"{selected_vendor} risk trend",
            )
            st.plotly_chart(fig, use_container_width=True)

    with notes_col:
        st.markdown("**Recommended actions**")
        outcome_record = latest_outcome.iloc[0] if not latest_outcome.empty else None
        action_points = dashboard._risk_action_recommendations(selected, outcome_record)
        for line in action_points:
            st.markdown(f"- {line}")

        if not latest_outcome.empty:
            record = latest_outcome.iloc[0]
            st.markdown("**Latest business outcome**")
            st.markdown(
                f"- Period: `{record['period']}`\n"
                f"- Relationship health: `{record['relationship_health']}`\n"
                f"- Incidents: `{int(record['incident_count'])}`\n"
                f"- Escalation: `{int(record['escalation_flag'])}`\n"
                f"- Churned: `{int(record['churned'])}`"
            )
        if pd.notna(trend_delta):
            st.markdown(f"**Trend delta**: `{trend_delta:+.1f}` points vs previous assessment")

    st.divider()

    bottom_left, bottom_right = st.columns([1.1, 1.2])
    with bottom_left:
        st.subheader("Risk Heatmap")
        risk_pivot = filtered[["vendor_name", "financial_risk", "operational_risk", "compliance_risk"]].set_index("vendor_name")
        fig = go.Figure(
            go.Heatmap(
                z=risk_pivot.values,
                x=risk_pivot.columns.tolist(),
                y=risk_pivot.index.tolist(),
                colorscale="Reds",
                text=risk_pivot.values.round(1),
                texttemplate="%{text}",
                textfont={"size": 9},
            )
        )
        fig.update_layout(height=max(300, len(filtered) * 22), yaxis_autorange="reversed", title="Risk scores by component")
        st.plotly_chart(fig, use_container_width=True)

    with bottom_right:
        st.subheader("Leadership Review Table")
        review_cols = [
            c
            for c in [
                "vendor_name",
                "category",
                "review_priority",
                "risk_level",
                "overall_risk",
                "financial_risk",
                "operational_risk",
                "compliance_risk",
                "mitigation_status",
                "incident_flag",
                "risk_delta",
            ]
            if c in filtered.columns
        ]
        st.dataframe(filtered[review_cols].round(2), use_container_width=True)

    if not risk_history.empty:
        st.divider()
        st.subheader("Portfolio Trend")
        hist_filtered = risk_history[risk_history["vendor_name"].isin(filtered["vendor_name"])]
        trend_frame = (
            hist_filtered.groupby("assessment_date")
            .agg(
                avg_overall_risk=("overall_risk", "mean"),
                avg_financial_risk=("financial_risk", "mean"),
                vendors=("vendor_name", "nunique"),
            )
            .reset_index()
            .sort_values("assessment_date")
        )
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                name="Avg overall risk",
                x=trend_frame["assessment_date"],
                y=trend_frame["avg_overall_risk"],
                mode="lines+markers",
                line=dict(color="#1f3c88", width=3),
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                name="Avg financial risk",
                x=trend_frame["assessment_date"],
                y=trend_frame["avg_financial_risk"],
                mode="lines+markers",
                line=dict(color="#ef4444", width=2),
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Bar(
                name="Vendors tracked",
                x=trend_frame["assessment_date"],
                y=trend_frame["vendors"],
                marker_color="#cbd5e1",
                opacity=0.5,
            ),
            secondary_y=True,
        )
        fig.update_layout(height=360, title="Assessment trend across the filtered portfolio")
        fig.update_yaxes(title_text="Risk (%)", secondary_y=False)
        fig.update_yaxes(title_text="Vendor count", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

