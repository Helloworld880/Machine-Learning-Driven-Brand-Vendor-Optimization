from datetime import datetime
import json

import pandas as pd
try:
    import plotly.express as px
    _PLOTLY_AVAILABLE = True
    _PLOTLY_IMPORT_ERROR = None
except ImportError as e:
    px = None
    _PLOTLY_AVAILABLE = False
    _PLOTLY_IMPORT_ERROR = e
import streamlit as st

import ai_integration as ai_tools
from ai_integration import (
    ReportSummaryGenerator,
    SmartAlertEngine,
    VendorDataChat,
    ExecutiveBriefBuilder,      # NEW
    VendorNarrativeEngine,      # NEW
    streamlit_chat_widget,
)


# ───────────── FORMATTING HELPERS ─────────────

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


def _tone_from_level(level: str) -> str:
    return {
        "High": "high", "Medium": "medium", "Low": "low",
        "Critical": "high", "Needs Attention": "medium", "Positive": "low",
    }.get(str(level), "neutral")


def _metric_delta(current, previous):
    try:
        return float(current) - float(previous)
    except Exception:
        return 0.0


def _risk_memo(vendor_row) -> str:
    vendor = vendor_row.get("vendor_name", "Vendor")
    risk_level = vendor_row.get("risk_level", "Unknown")
    overall = _format_pct(vendor_row.get("overall_risk"))
    performance = _format_pct(vendor_row.get("performance_score"))
    compliance = _format_pct(vendor_row.get("compliance_score"))
    cost = _fmt_currency(vendor_row.get("cost_variance", 0))
    mitigation = vendor_row.get("mitigation_status", "Monitoring")
    return (
        f"{vendor} is currently assessed as {risk_level} risk with an overall risk score of {overall}. "
        f"Performance is running at {performance}, compliance is at {compliance}, and current cost variance is {cost}. "
        f"The current mitigation status is {mitigation}. Leadership should confirm owner accountability, lock the next review date, "
        f"and validate whether this vendor remains in weekly monitoring or moves to formal escalation."
    )


def _executive_pack(brief_result) -> str:
    """Build the full text pack from a BriefResult object."""
    return brief_result.as_text()


def _priority_reasons(vendor_row) -> list[str]:
    reasons = []
    if float(vendor_row.get("overall_risk", 0) or 0) >= 70:
        reasons.append("Overall vendor risk is already in the escalation zone.")
    if float(vendor_row.get("compliance_score", 100) or 100) < 70:
        reasons.append("Compliance is below the acceptable threshold.")
    if float(vendor_row.get("performance_score", 100) or 100) < 70:
        reasons.append("Operational performance is under target.")
    if float(vendor_row.get("cost_variance", 0) or 0) > 50000:
        reasons.append("Cost variance is materially higher than expected.")
    if str(vendor_row.get("compliance_status", "")).lower() in {"non-compliant", "under review"}:
        reasons.append("Compliance status still needs active follow-up.")
    if not reasons:
        reasons.append("Combined risk, performance, and compliance pressure places this vendor at the top of the queue.")
    return reasons[:3]


def _what_this_tab_does(title: str, purpose: str, output: str):
    st.markdown(
        f"""
        <div class="insight-box">
            <div class="insight-title">{title}</div>
            <div><strong>Use this when:</strong> {purpose}</div>
            <div style="margin-top:6px;"><strong>You will get:</strong> {output}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ───────────── SECTION CARD RENDERER ─────────────

def _brief_section_card(icon: str, title: str, body: str, border_color: str = "#3b82f6"):
    st.markdown(
        f"""
        <div style="
            border-left: 5px solid {border_color};
            background: #f9fafb;
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 14px;
        ">
            <div style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.07em;
                        color:{border_color};font-weight:700;margin-bottom:4px;">
                {icon} {title}
            </div>
            <div style="color:#1f2937;line-height:1.6;font-size:0.97rem;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════════════════

def render_ai_workspace(dashboard):
    if not _PLOTLY_AVAILABLE:
        st.error("Plotly is not available in the current deployment, so the AI workspace charts cannot load.")
        if _PLOTLY_IMPORT_ERROR is not None:
            st.caption(f"Import error: {_PLOTLY_IMPORT_ERROR}")
        return
    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-kicker">AI Command Center</div>
            <div class="hero-title">Turn vendor risk signals into executive-ready actions</div>
            <p class="hero-copy">
                This workspace is powered by Claude (Anthropic API). Use it to identify
                priority vendors, generate leadership briefs, explain alerts, and ask your portfolio
                questions in one place.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Mode: `{ai_tools.AI_MODE}` | Last backend: `{ai_tools.LAST_AI_BACKEND}`")

    # ── Architecture map (unchanged) ─────────────────────────────────────────
    st.markdown(
        """
        <div class="ai-map">
            <div class="ai-map-title">AI Insights — where it fits in VendorInsight360</div>
            <div class="ai-map-box ai-map-wide">
                <div class="ai-map-head">Data layer</div>
                <div class="ai-map-sub">vendors.db, vendors.csv, performance.csv, financial_metrics.csv, compliance_history.csv, risk_history.csv</div>
            </div>
            <div class="ai-map-arrow">↓</div>
            <div class="ai-map-box ai-map-core">
                <div class="ai-map-head">AI Insights engine</div>
                <div class="ai-map-sub">ai_integration.py · Claude (Anthropic API) · portfolio context assembly</div>
            </div>
            <div class="ai-map-grid">
                <div class="ai-map-box ai-map-green">
                    <div class="ai-map-head">Health scorecards</div>
                    <div class="ai-map-sub">Explain vendor strength, weakness, and intervention need.</div>
                </div>
                <div class="ai-map-box ai-map-amber">
                    <div class="ai-map-head">Risk flagging</div>
                    <div class="ai-map-sub">Spot compliance gaps, cost pressure, and escalation cases early.</div>
                </div>
                <div class="ai-map-box ai-map-rust">
                    <div class="ai-map-head">Structured briefs</div>
                    <div class="ai-map-sub">Audience-aware executive briefs with named sections and download.</div>
                </div>
                <div class="ai-map-box ai-map-blue">
                    <div class="ai-map-head">Chat assistant</div>
                    <div class="ai-map-sub">Multi-turn reasoning with follow-up suggestions after every answer.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("How the AI works", expanded=False):
        st.markdown(
            "- **real (current)**: Anthropic Claude API — full reasoning, structured output, multi-turn memory\n"
            "- **auto**: tries local Ollama first, then mock fallback\n"
            "- **ollama**: local model only (no external calls)\n"
            "- **mock**: rule-based demo mode (no external calls)\n"
        )

    perf_df, fin_df, perf_history, compliance, risk = dashboard._get_ai_dataframes()
    review = dashboard._get_risk_review_frame()

    if perf_df.empty or review.empty:
        st.warning("AI tools need vendor performance/risk data. Check sidebar → **Data Health** to confirm rows are present.")
        return

    # ── Portfolio KPIs ────────────────────────────────────────────────────────
    top3 = review.head(3)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Priority Vendors", len(review))
    k2.metric("High Risk Now", int((review["risk_level"] == "High").sum()))
    k3.metric("Below 70 Compliance", int((review["compliance_score"].fillna(100) < 70).sum()))
    k4.metric("Average Priority Score", f"{review['priority_score'].mean():.1f}")

    st.divider()

    # ── Top queue + quick executive takeaways ─────────────────────────────────
    left, right = st.columns([1.1, 1.4])
    with left:
        st.subheader("Top Review Queue")
        st.caption("Vendors needing fastest attention based on risk, performance, and compliance.")
        for _, row in top3.iterrows():
            dashboard._render_priority_card(row)

    with right:
        st.subheader("Quick Executive Takeaways")
        generator = ReportSummaryGenerator()
        with st.spinner("Generating executive summary…"):
            exec_summary = generator.generate(
                vendor_df=perf_df,
                period=datetime.now().strftime("%b %Y"),
                financial_df=fin_df if not fin_df.empty else None,
                history_df=perf_history if not perf_history.empty else None,
                summary_type="executive",
            )
        st.markdown(exec_summary)
        if not top3.empty:
            action_lines = [
                f"Prioritize **{row['vendor_name']}** — priority score {row['priority_score']}."
                for _, row in top3.iterrows()
            ]
            st.info("\n".join(action_lines))
        st.caption(f"Backend: `{ai_tools.LAST_AI_BACKEND}`")

    # ── Task selector ─────────────────────────────────────────────────────────
    st.markdown("**Choose what you need today**")
    task_map = {
        "🔍 Review risky vendors": "risk_review",
        "💬 Ask the data a question": "ask_data",
        "📋 Build an executive brief": "executive_brief",
        "🔔 Explain an alert": "alert_studio",
    }
    task_choice = st.radio(
        "AI task", list(task_map.keys()),
        horizontal=True, label_visibility="collapsed", key="ai_task_choice",
    )
    active_task = task_map[task_choice]
    st.caption(f"Current task: **{task_choice}**")

    # ═════════════════════════════════════════════════════════════════════════
    # TASK 1 — RISK REVIEW  (+ NEW: Vendor Narrative section)
    # ═════════════════════════════════════════════════════════════════════════
    if active_task == "risk_review":
        st.subheader("Risk Review Workflow")
        _what_this_tab_does(
            "What this tab does",
            "you need to know which vendor deserves attention first, what is driving the concern, and what to do next.",
            "a ranked review, AI health narrative, peer comparison, action checklist, and a downloadable memo.",
        )

        vendor_options = review["vendor_name"].tolist()
        selected_vendor = st.selectbox("Select priority vendor", vendor_options, key="hero_risk_vendor")
        vendor_row = review[review["vendor_name"] == selected_vendor].iloc[0]

        peer_set = review[review["category"] == vendor_row.get("category")].copy()
        peer_avg_perf = float(peer_set["performance_score"].mean()) if not peer_set.empty else float(vendor_row.get("performance_score", 0))
        peer_avg_comp = float(peer_set["compliance_score"].mean()) if not peer_set.empty else float(vendor_row.get("compliance_score", 0))
        peer_avg_risk = float(peer_set["overall_risk"].mean()) if not peer_set.empty else float(vendor_row.get("overall_risk", 0))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Risk", _format_pct(vendor_row.get("overall_risk")))
        c2.metric("Performance", _format_pct(vendor_row.get("performance_score")),
                  f"{_metric_delta(vendor_row.get('performance_score', 0), peer_avg_perf):+.1f} vs peers")
        c3.metric("Compliance", _format_pct(vendor_row.get("compliance_score")),
                  f"{_metric_delta(vendor_row.get('compliance_score', 0), peer_avg_comp):+.1f} vs peers")
        c4.metric("Cost Variance", _fmt_currency(vendor_row.get("cost_variance", 0) or 0))

        compare1, compare2, compare3 = st.columns(3)
        compare1.metric("Peer Avg Risk", _format_pct(peer_avg_risk))
        compare2.metric("Peer Avg Performance", _format_pct(peer_avg_perf))
        compare3.metric("Peer Avg Compliance", _format_pct(peer_avg_comp))

        # ── NEW: AI Vendor Health Narrative ──────────────────────────────────
        st.markdown("---")
        st.markdown("**🤖 AI Vendor Health Narrative**")
        st.caption("One-click AI assessment of this vendor's health, risk drivers, and recommended intervention.")

        if st.button("Generate health narrative", key="gen_narrative", type="primary"):
            narrative_engine = VendorNarrativeEngine()
            peer_averages = {
                "avg_performance": peer_avg_perf,
                "avg_compliance": peer_avg_comp,
                "avg_risk": peer_avg_risk,
            }
            vendor_history = pd.DataFrame()
            if not perf_history.empty and "vendor_name" in perf_history.columns:
                vendor_history = perf_history[perf_history["vendor_name"] == selected_vendor].copy()

            with st.spinner("Generating vendor health narrative…"):
                narrative = narrative_engine.narrate(
                    vendor_row=vendor_row.to_dict(),
                    peer_averages=peer_averages,
                    history_df=vendor_history if not vendor_history.empty else None,
                )
            st.markdown(
                f"""
                <div style="background:#f0f7ff;border:1px solid #bfdbfe;border-radius:14px;
                            padding:18px 20px;margin-top:8px;color:#1e3a5f;line-height:1.7;">
                    {narrative.replace(chr(10), '<br>')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(f"Backend: `{ai_tools.LAST_AI_BACKEND}`")
        st.markdown("---")

        st.markdown("**Why this vendor is in focus**")
        for reason in _priority_reasons(vendor_row):
            st.markdown(f"- {reason}")

        r1, r2 = st.columns([1.2, 1])
        with r1:
            focus_cols = [c for c in ["financial_risk", "operational_risk", "compliance_risk"] if c in review.columns]
            if focus_cols:
                focus_df = pd.DataFrame(
                    {"risk_component": focus_cols, "score": [vendor_row.get(c, 0) for c in focus_cols]}
                )
                fig = px.bar(focus_df, x="risk_component", y="score",
                             color="score", color_continuous_scale="Reds",
                             title=f"{selected_vendor} risk component view")
                st.plotly_chart(fig, use_container_width=True)

            if not perf_history.empty and "vendor_name" in perf_history.columns:
                v_hist = perf_history[perf_history["vendor_name"] == selected_vendor].sort_values("metric_date")
                if not v_hist.empty:
                    fig = px.line(v_hist, x="metric_date", y="overall_score", markers=True,
                                  title=f"{selected_vendor} performance trend")
                    st.plotly_chart(fig, use_container_width=True)

        with r2:
            st.markdown("**Action checklist**")
            for line in dashboard._risk_action_recommendations(vendor_row):
                st.markdown(f"- {line}")

            st.markdown("**Leadership summary**")
            leadership_note = dashboard._risk_leadership_note(
                vendor_row,
                vendor_row.get("overall_risk", 0) - vendor_row.get("priority_score", 0),
            )
            st.markdown(leadership_note)

        memo = _risk_memo(vendor_row)
        st.markdown("**Escalation memo draft**")
        st.code(memo)
        st.download_button(
            "Download escalation memo", memo.encode("utf-8"),
            file_name=f"{selected_vendor.lower().replace(' ', '_')}_escalation_memo.txt",
            mime="text/plain", use_container_width=True,
        )

        spotlight = review.head(8).copy()
        spotlight["priority_band"] = spotlight["risk_level"].map(
            lambda lvl: "Escalate Now" if lvl == "High" else "Monitor Closely"
        )
        st.markdown("**Queue spotlight**")
        st.dataframe(
            spotlight[["vendor_name", "category", "priority_score", "risk_level",
                        "overall_risk", "compliance_score", "priority_band"]].round(2),
            use_container_width=True,
        )

    # ═════════════════════════════════════════════════════════════════════════
    # TASK 2 — ASK DATA  (upgraded: follow-up chips, step-by-step chat)
    # ═════════════════════════════════════════════════════════════════════════
    elif active_task == "ask_data":
        st.subheader("Ask Your Vendor Data")
        _what_this_tab_does(
            "What this tab does",
            "you want a quick, reasoned answer from the vendor portfolio without reading tables manually.",
            "a direct answer with step-by-step reasoning, data values, and an automatic follow-up suggestion.",
        )
        st.caption(
            "Claude reasons through the data before answering. "
            "Each answer ends with a suggested follow-up you can tap to continue the conversation."
        )

        # ── Quick-fire prompt chips ───────────────────────────────────────────
        qcol1, qcol2, qcol3, qcol4 = st.columns(4)
        if qcol1.button("Compliance watchlist", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which vendors have compliance below 70% and what are their scores?"
        if qcol2.button("Cost pressure", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which vendor has the highest cost variance and what is the exact value?"
        if qcol3.button("Top 3 at-risk", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which are the top 3 at-risk vendors and what specifically makes each one high risk?"
        if qcol4.button("Best vendors", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Who are the best-performing vendors across quality, compliance, and delivery? Rank them."

        # ── Extra context chips ───────────────────────────────────────────────
        ec1, ec2, ec3 = st.columns(3)
        if ec1.button("Escalation candidates", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which vendors are most likely to need formal escalation this month and why?"
        if ec2.button("Risk + cost overlap", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Which vendor combines the lowest compliance score with the highest cost variance?"
        if ec3.button("Portfolio health", use_container_width=True):
            st.session_state["__ai_suggested_prompt"] = "Summarise the overall portfolio health in 3 key points with specific numbers."

        tcol1, tcol2 = st.columns([1, 1])
        vendor_scope = tcol1.selectbox("Scope", ["All vendors", "Single vendor"], key="ai_chat_scope")
        scoped_vendor = None
        if vendor_scope == "Single vendor":
            scoped_vendor = tcol2.selectbox(
                "Vendor", sorted(review["vendor_name"].dropna().unique().tolist()), key="ai_chat_vendor"
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

        chat = VendorDataChat(
            scoped_perf,
            scoped_fin if scoped_fin is not None and not scoped_fin.empty else pd.DataFrame(),
            labels=["performance", "financial"],
        )

        if st.session_state.get("__ai_suggested_prompt"):
            st.info(f"Suggested prompt loaded — paste into the input below: `{st.session_state['__ai_suggested_prompt']}`")

        # ── Portfolio pulse metrics ───────────────────────────────────────────
        insight1, insight2, insight3 = st.columns(3)
        top_risk_vendor = review.sort_values("overall_risk", ascending=False).iloc[0]
        top_cost_vendor = review.sort_values("cost_variance", ascending=False).iloc[0]
        low_compliance = review.sort_values("compliance_score").iloc[0]
        insight1.metric("Highest Risk Vendor", top_risk_vendor["vendor_name"],
                         _format_pct(top_risk_vendor["overall_risk"]))
        insight2.metric("Highest Cost Pressure", top_cost_vendor["vendor_name"],
                         _fmt_currency(top_cost_vendor["cost_variance"]))
        insight3.metric("Lowest Compliance", low_compliance["vendor_name"],
                         _format_pct(low_compliance["compliance_score"]))

        # ── Chat widget (includes follow-up chip) ─────────────────────────────
        streamlit_chat_widget(chat)

        with st.expander("Good question formats", expanded=False):
            st.markdown(
                "- Which vendors are most likely to need escalation this month?\n"
                "- Which vendor combines low compliance and high cost variance?\n"
                "- Which vendors are strongest by combined delivery, quality, and compliance?\n"
                "- Summarize the biggest procurement risks in 3 points with numbers.\n"
                "- How has Vendor X's performance trended over the last 3 periods?\n"
                "- Which category has the worst average compliance score?"
            )

    # ═════════════════════════════════════════════════════════════════════════
    # TASK 3 — EXECUTIVE BRIEF  (full upgrade: structured sections, audience/tone)
    # ═════════════════════════════════════════════════════════════════════════
    elif active_task == "executive_brief":
        st.subheader("Executive Brief Builder")
        _what_this_tab_does(
            "What this tab does",
            "you need to update leadership, procurement, or operations on the current vendor situation.",
            "a structured brief with named sections (Situation / Key Findings / Risk Outlook / Actions) tailored to your audience and tone — ready to copy or download.",
        )

        # ── Configuration row ─────────────────────────────────────────────────
        bcfg1, bcfg2, bcfg3, bcfg4 = st.columns(4)
        brief_type = bcfg1.selectbox(
            "Brief focus", ["executive", "compliance", "financial", "risk"], key="hero_brief_type"
        )
        audience = bcfg2.selectbox(
            "Audience", ["board", "procurement", "operations"], key="brief_audience"
        )
        tone = bcfg3.selectbox(
            "Tone", ["formal", "direct", "operational"], key="brief_tone"
        )
        period_label = bcfg4.text_input("Period label", value=datetime.now().strftime("%b %Y"), key="brief_period")

        # ── Audience guide ────────────────────────────────────────────────────
        audience_guide = {
            "board": "Financial exposure, strategic risk, governance implications. Dollar-denominated.",
            "procurement": "Vendor metrics, contract risk, compliance gaps, sourcing decisions.",
            "operations": "SLA risk, delivery reliability, capacity concerns, hands-on escalation.",
        }
        st.caption(f"**{audience.title()} brief:** {audience_guide.get(audience, '')}")

        # ── Portfolio KPIs for context ────────────────────────────────────────
        brief_k1, brief_k2, brief_k3 = st.columns(3)
        brief_k1.metric("High-Risk Vendors", int((review["risk_level"] == "High").sum()))
        brief_k2.metric("Priority Queue Size", len(review.head(10)))
        brief_k3.metric("Average Compliance", _format_pct(review["compliance_score"].mean()))

        st.divider()

        if st.button("Generate structured brief", use_container_width=True, type="primary", key="gen_brief_btn"):
            builder = ExecutiveBriefBuilder()
            with st.spinner("Building executive brief…"):
                brief = builder.build(
                    vendor_df=perf_df,
                    review_df=review,
                    period=period_label,
                    audience=audience,
                    tone=tone,
                    financial_df=fin_df if not fin_df.empty else None,
                    history_df=perf_history if not perf_history.empty else None,
                )

            # ── Render structured sections ────────────────────────────────────
            st.markdown(f"**{audience.title()} Brief · {period_label} · {tone.title()} tone**")
            _brief_section_card("📍", "Situation", brief.situation, border_color="#3b82f6")
            _brief_section_card("🔎", "Key Findings", brief.key_findings, border_color="#f59e0b")
            _brief_section_card("📈", "Risk Outlook", brief.risk_outlook, border_color="#ef4444")
            _brief_section_card("✅", "Recommended Actions", brief.recommended_actions, border_color="#22c55e")

            # ── Download ──────────────────────────────────────────────────────
            full_text = brief.as_text()
            st.download_button(
                "📥 Download brief as text", full_text.encode("utf-8"),
                file_name=f"{audience}_{brief_type}_brief_{period_label.replace(' ', '_')}.txt",
                mime="text/plain", use_container_width=True,
            )
            st.caption(f"Backend: `{ai_tools.LAST_AI_BACKEND}`")

        # ── Also offer the legacy narrative-style brief ───────────────────────
        with st.expander("Alternative: narrative-style summary", expanded=False):
            if st.button("Generate narrative summary", key="gen_narrative_brief"):
                generator = ReportSummaryGenerator()
                with st.spinner("Generating narrative…"):
                    summary = generator.generate(
                        vendor_df=perf_df,
                        period=period_label,
                        financial_df=fin_df if not fin_df.empty else None,
                        history_df=perf_history if not perf_history.empty else None,
                        summary_type=brief_type,
                    )
                st.markdown(summary)
                top_lines = "\n".join(
                    f"- **{row['vendor_name']}**: priority score {row.get('priority_score', '—')}"
                    for _, row in review.head(5).iterrows()
                )
                st.markdown("**Top priority vendors**\n" + top_lines)
                st.caption(f"Backend: `{ai_tools.LAST_AI_BACKEND}`")

    # ═════════════════════════════════════════════════════════════════════════
    # TASK 4 — ALERT STUDIO  (unchanged, kept intact)
    # ═════════════════════════════════════════════════════════════════════════
    elif active_task == "alert_studio":
        st.subheader("Alert Studio")
        _what_this_tab_does(
            "What this tab does",
            "a score moved and you need to explain the change without writing the note manually.",
            "a readable alert summary with what happened, why it matters, and what to do next.",
        )
        engine = SmartAlertEngine()
        alert_vendor = st.selectbox("Vendor", review["vendor_name"].tolist(), key="alert_vendor")
        vendor_row = review[review["vendor_name"] == alert_vendor].iloc[0]
        metric_choice = st.selectbox(
            "Metric", ["compliance score", "performance score", "overall risk"], key="alert_metric_choice"
        )

        threshold = 70.0 if metric_choice != "overall risk" else 60.0
        prev_val = cur_val = None

        if metric_choice == "compliance score":
            cur_val = float(vendor_row.get("compliance_score", 0) or 0)
            prev_val = cur_val
            if compliance is not None and not compliance.empty and "vendor_name" in compliance.columns:
                v_hist = compliance[compliance["vendor_name"] == alert_vendor].copy()
                if not v_hist.empty:
                    date_col = "audit_date" if "audit_date" in v_hist.columns else None
                    score_col = "audit_score" if "audit_score" in v_hist.columns else (
                        "compliance_score" if "compliance_score" in v_hist.columns else None
                    )
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

        else:
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
        change = _metric_delta(cur_val, prev_val)

        a1, a2, a3 = st.columns(3)
        a1.metric("Previous", f"{prev_val:.1f}")
        a2.metric("Current", f"{cur_val:.1f}", f"{change:+.1f}")
        a3.metric("Threshold", f"{threshold:.1f}")

        if st.button("Explain alert", use_container_width=True):
            with st.spinner("Generating alert explanation…"):
                alert = engine.explain(
                    vendor_name=alert_vendor, metric=metric_choice,
                    current_value=cur_val, previous_value=prev_val, threshold=threshold,
                )
            tone = _tone_from_level(
                getattr(alert, "severity", "neutral").title() if hasattr(alert, "severity") else "neutral"
            )
            st.markdown("**What happened / Why it matters / What to do now**")
            st.markdown(
                f"- **What happened:** {metric_choice.title()} moved from {prev_val:.1f} to {cur_val:.1f}.\n"
                f"- **Why it matters:** {alert.explanation}\n"
                f"- **What to do now:** {alert.recommendation}"
            )
            st.markdown(
                f"""
                <div class="priority-card priority-{tone}">
                    <div class="pill pill-{tone}">{getattr(alert, 'severity', 'info').upper()}</div>
                    <div style="font-size:1.1rem;font-weight:800;color:#12264d;margin-top:8px;">{alert.headline}</div>
                    <div style="color:#4b5563;margin-top:6px;"><strong>Explanation:</strong> {alert.explanation}</div>
                    <div style="color:#4b5563;margin-top:6px;"><strong>Recommendation:</strong> {alert.recommendation}</div>
                    <div style="color:#4b5563;margin-top:6px;"><strong>Urgency:</strong> {alert.urgency}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            plain_note = (
                f"Subject: {alert.email_subject}\n\n"
                f"Headline: {alert.headline}\n"
                f"Metric: {metric_choice}\n"
                f"Previous: {prev_val:.1f}\n"
                f"Current: {cur_val:.1f}\n"
                f"Threshold: {threshold:.1f}\n\n"
                f"Explanation: {alert.explanation}\n"
                f"Recommendation: {alert.recommendation}\n"
                f"Urgency: {alert.urgency}\n"
            )
            st.code(plain_note)
            st.download_button(
                "Download alert note", plain_note.encode("utf-8"),
                file_name=f"{alert_vendor.lower().replace(' ', '_')}_{metric_choice.replace(' ', '_')}_alert.txt",
                mime="text/plain", use_container_width=True,
            )
            st.caption(f"Backend: `{ai_tools.LAST_AI_BACKEND}`")
