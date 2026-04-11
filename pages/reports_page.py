import os
from datetime import datetime

import pandas as pd
import streamlit as st


def render_reports(dashboard):
    st.markdown('<div class="main-header">📄 Reports & Export</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-kicker">Decision Pack</div>
            <div class="hero-title">Generate a business-ready risk review pack</div>
            <p class="hero-copy">
                Use this workflow to export leadership notes, supporting data, and formal reports from one place.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    review = dashboard._get_risk_review_frame()
    if not review.empty:
        selected_vendor = st.selectbox("Leadership brief vendor", review["vendor_name"].tolist(), key="report_vendor")
        selected_row = review[review["vendor_name"] == selected_vendor].iloc[0]
        note = dashboard._risk_leadership_note(selected_row, selected_row.get("overall_risk", 0) - selected_row.get("priority_score", 0))
        action_lines = dashboard._risk_action_recommendations(selected_row)
        pack_text = "\n".join(
            [
                f"Risk Review Pack - {selected_vendor}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "",
                "Leadership Note",
                note,
                "",
                "Recommended Actions",
                *[f"- {line}" for line in action_lines],
            ]
        )
        st.subheader("Risk Review Pack")
        st.code(pack_text)
        st.download_button(
            "Download risk review pack",
            pack_text.encode("utf-8"),
            file_name=f"{selected_vendor.lower().replace(' ', '_')}_risk_review_pack.txt",
            mime="text/plain",
            use_container_width=True,
        )

    if not dashboard.report_gen:
        st.error("Report generator not available. Install: `pip install reportlab xlsxwriter`")
        return

    col1, col2, col3 = st.columns(3)
    report_type = col1.selectbox(
        "Report Type",
        ["Vendor Performance", "Financial Summary", "Risk Assessment", "Compliance Status", "Executive Summary"],
    )
    fmt = col2.selectbox("Format", ["PDF", "Excel", "HTML"])
    col3.markdown("<br>", unsafe_allow_html=True)
    if col3.button("📊 Generate Report", type="primary", use_container_width=True):
        with st.spinner("Generating…"):
            result = dashboard.report_gen.generate_report(report_type, fmt)
        if "✅" in result or "generated" in result.lower():
            fpath = result.split(":")[-1].strip()
            st.success(f"✅ Report generated: `{fpath}`")
            try:
                with open(fpath, "rb") as handle:
                    data = handle.read()
                mime_map = {
                    "PDF": "application/pdf",
                    "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "HTML": "text/html",
                }
                st.download_button(
                    f"⬇️ Download {fmt}",
                    data,
                    os.path.basename(fpath),
                    mime_map.get(fmt, "application/octet-stream"),
                )
                if fmt == "HTML":
                    with open(fpath, "r", encoding="utf-8") as handle:
                        st.components.v1.html(handle.read(), height=600, scrolling=True)
            except Exception as exc:
                st.error(f"Could not read file: {exc}")
        else:
            st.error(result)

    st.divider()
    st.subheader("📂 Previously Generated Reports")
    reports = dashboard.report_gen.get_generated_reports()
    if reports:
        df_rep = pd.DataFrame(reports)
        df_rep["size"] = df_rep["size"].apply(lambda x: f"{x/1024:.1f} KB")
        st.dataframe(df_rep[["name", "size", "created"]], use_container_width=True)
    else:
        st.info("No reports generated yet.")
