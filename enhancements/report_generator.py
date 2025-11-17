import os
import tempfile
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
from core_modules.database import DatabaseManager


class ReportGenerator:
    """Dashboard-style report generator with Unicode-safe DejaVu fonts."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    # -------------------------------------------------
    # FETCH GENERATED REPORTS
    # -------------------------------------------------
    def get_generated_reports(self):
        """Return metadata for previously generated reports."""
        reports = []
        if not os.path.exists(self.reports_dir):
            return reports
        for f in os.listdir(self.reports_dir):
            if f.lower().endswith((".pdf", ".xlsx", ".html")):
                path = os.path.join(self.reports_dir, f)
                reports.append({
                    "name": f,
                    "path": path,
                    "size": f"{os.path.getsize(path) / 1024:.1f} KB",
                    "created": datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d %H:%M")
                })
        return sorted(reports, key=lambda x: x["created"], reverse=True)

    # -------------------------------------------------
    # MAIN ENTRY POINT
    # -------------------------------------------------
    def generate_report(self, report_type: str, format_type: str) -> str:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext_map = {"PDF": "pdf"}
            ext = ext_map.get(format_type.upper(), "pdf")
            filename = f"{report_type.replace(' ', '_')}_{ts}.{ext}"
            filepath = os.path.join(self.reports_dir, filename)
            return self._generate_dashboard_pdf(report_type, filepath)
        except Exception as e:
            return f"❌ Error generating report: {e}"

    # -------------------------------------------------
    # DASHBOARD PDF GENERATION
    # -------------------------------------------------
    def _generate_dashboard_pdf(self, report_type, filepath):
        """Generates a professional dashboard-style PDF report."""
        try:
            vendors = getattr(self.db, "get_vendors", lambda: pd.DataFrame())()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Font Setup (Unicode-safe)
            font_dir = os.path.join(self.reports_dir)
            regular = os.path.join(font_dir, "DejaVuSans.ttf")
            bold = os.path.join(font_dir, "DejaVuSans-Bold.ttf")
            italic = os.path.join(font_dir, "DejaVuSans-Oblique.ttf")
            font_name = "Arial"

            if os.path.exists(regular):
                try:
                    pdf.add_font("DejaVu", "", regular, uni=True)
                    if os.path.exists(bold):
                        pdf.add_font("DejaVu", "B", bold, uni=True)
                    if os.path.exists(italic):
                        pdf.add_font("DejaVu", "I", italic, uni=True)
                    font_name = "DejaVu"
                except Exception as e:
                    print(f"⚠️ Font load failed: {e}")

            def t(s): return str(s).encode("latin-1", "ignore").decode("latin-1")

            # HEADER
            pdf.set_fill_color(30, 60, 120)
            pdf.rect(0, 0, 210, 25, "F")
            pdf.set_text_color(255, 255, 255)
            pdf.set_font(font_name, "B", 18)
            pdf.cell(0, 15, t(f"{report_type} Dashboard"), ln=True, align="C")
            pdf.set_font(font_name, "", 10)
            pdf.cell(0, 10, t(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"), ln=True, align="C")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(10)

            # SUMMARY METRICS
            total = len(vendors)
            active = vendors[vendors["status"].str.lower() == "active"].shape[0] if "status" in vendors else total
            high_risk = vendors[vendors["risk_level"].str.lower() == "high"].shape[0] if "risk_level" in vendors else 0
            total_value = vendors["contract_value"].sum() if "contract_value" in vendors else 0

            pdf.set_font(font_name, "B", 12)
            pdf.cell(0, 10, t("Executive Summary"), ln=True)
            pdf.ln(4)

            def kpi(label, value, color):
                pdf.set_fill_color(*color)
                pdf.cell(95, 12, t(f"{label}: {value}"), border=1, ln=0, align="C", fill=True)

            kpi("Total Vendors", total, (220, 240, 255))
            kpi("Active Vendors", active, (220, 255, 220))
            pdf.ln(12)
            kpi("High Risk Vendors", high_risk, (255, 220, 220))
            kpi("Total Contract Value", f"${total_value:,.0f}", (255, 245, 200))
            pdf.ln(16)

            # CHART
            if not vendors.empty and "contract_value" in vendors and "name" in vendors:
                top_vendors = vendors.nlargest(6, "contract_value")
                plt.figure(figsize=(7, 3))
                plt.barh(top_vendors["name"], top_vendors["contract_value"], color="#1f77b4")
                plt.xlabel("Contract Value ($)")
                plt.title("Top Vendors by Contract Value", fontsize=10)
                plt.tight_layout()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as chart:
                    plt.savefig(chart.name, bbox_inches="tight", dpi=120)
                    chart_path = chart.name
                plt.close()
                pdf.image(chart_path, x=10, w=190)
                os.remove(chart_path)
                pdf.ln(10)

            # INSIGHTS
            pdf.set_font(font_name, "B", 12)
            pdf.cell(0, 10, t("Insights & Recommendations"), ln=True)
            pdf.set_font(font_name, "", 10)
            pdf.multi_cell(0, 6, t(
                "• High-risk vendors require immediate review.\n"
                "• Optimize contract distribution to balance dependency.\n"
                "• Conduct performance audits for vendors with low contract value.\n"
                "• Consider rewarding top-performing vendors with renewals.\n"
                "• Consolidate vendors to reduce cost duplication."
            ))
            pdf.ln(10)

            # TABLE
            if not vendors.empty:
                pdf.set_font(font_name, "B", 11)
                pdf.cell(0, 10, t("Vendor Summary (Top 10)"), ln=True)
                pdf.set_font(font_name, "", 8)
                cols = [c for c in ["name", "category", "contract_value", "risk_level", "status"] if c in vendors]
                col_width = 190 / len(cols)
                pdf.set_fill_color(230, 230, 240)
                for c in cols:
                    pdf.cell(col_width, 8, t(c.title()), border=1, align="C", fill=True)
                pdf.ln()
                for _, r in vendors.head(10).iterrows():
                    for c in cols:
                        val = r[c]
                        if isinstance(val, (int, float)) and "value" in c:
                            val = f"${val:,.0f}"
                        pdf.cell(col_width, 6, t(str(val)[:25]), border=1, align="C")
                    pdf.ln()

            # FOOTER
            pdf.ln(8)
            pdf.set_font(font_name, "I", 8)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 6, t("Confidential — Internal Use Only"), align="C", ln=True)
            pdf.cell(0, 6, t(f"Vendor Management System | Page {pdf.page_no()}"), align="C")

            pdf.output(filepath)
            return f"✅ Dashboard PDF created successfully: {filepath}"

        except Exception as e:
            return f"❌ PDF generation failed: {e}"
