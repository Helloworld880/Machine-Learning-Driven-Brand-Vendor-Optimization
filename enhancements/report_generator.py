# enhancements/report_generator.py
"""
Robust ReportGenerator using DejaVu font, ReportLab, matplotlib, xlsxwriter and pandas.
- Loads DB data if available; otherwise loads specific dataset files from Data layer folder
- Produces PDF, Excel, and HTML outputs with header/footer, summary, charts and snapshot table.
"""

import os
import io
import base64
from datetime import datetime
from typing import Optional, Dict
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Excel writer
import xlsxwriter

# Configure matplotlib (do not set colors/styles globally - leave defaults)
plt.rcParams.update({'figure.max_open_warning': 0})

class ReportGenerator:
    def __init__(self, db):
        self.db = db
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)
        self.charts_dir = os.path.join(self.output_dir, "charts")
        os.makedirs(self.charts_dir, exist_ok=True)

        # Map report types to files in "Data layer" folder (note the space)
        self.forced_file_map = {
            "Vendor Performance": [
                "Data layer/vendors.csv", 
                "Data layer/performance.csv",
                "./Data layer/vendors.csv",
                "./Data layer/performance.csv"
            ],
            "Financial Summary": [
                "Data layer/financial_metrics.csv",
                "./Data layer/financial_metrics.csv"
            ],
            "Brand & ESG": [
                "Data layer/brand.csv",
                "./Data layer/brand.csv"
            ],
            "Risk Assessment": [
                "Data layer/industry_benchmarks.csv",
                "./Data layer/industry_benchmarks.csv"
            ],
            "Compliance Status": [
                "Data layer/vendors.csv",
                "./Data layer/vendors.csv"
            ],
            "Executive Summary": [
                "Data layer/vendors.csv",
                "./Data layer/vendors.csv"
            ],
        }

        # Font detection: prefer DejaVuSans in enhancements/fonts
        self.fonts_to_try = [
            os.path.join("enhancements", "fonts", "DejaVuSans.ttf"),
            r"C:\Users\yashd\Desktop\Machine-Learning-Driven-Brand-Vendor-Optimization\enhancements\fonts\DejaVuSans.ttf",
            r"C:\Users\yashd\Desktop\Machine-Learning-Driven-Brand-Vendor-Optimization\fonts\DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        self.default_title_font = "Helvetica-Bold"
        self.default_body_font = "Helvetica"
        self.font_ready = False
        for p in self.fonts_to_try:
            try:
                if p and os.path.exists(p):
                    pdfmetrics.registerFont(TTFont("DejaVuSans", p))
                    self.default_title_font = "DejaVuSans"
                    self.default_body_font = "DejaVuSans"
                    self.font_ready = True
                    break
            except Exception:
                continue

        # Styles for ReportLab
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name="ReportTitle", fontName=self.default_title_font, fontSize=18, leading=22, spaceAfter=12))
        self.styles.add(ParagraphStyle(name="NormalBody", fontName=self.default_body_font, fontSize=10, leading=12))
        self.styles.add(ParagraphStyle(name="Highlight", fontName=self.default_body_font, fontSize=11, leading=13, textColor=colors.HexColor("#1f77b4")))

    # -------------------------
    # Data loader (DB first, forced files second)
    # -------------------------
    def _get_report_data(self, report_type: str) -> pd.DataFrame:
        df = pd.DataFrame()
        print(f"[DEBUG] Fetching data for: {report_type}")
        
        # Try DB methods
        try:
            if report_type == "Vendor Performance":
                if hasattr(self.db, "get_vendors_with_performance"):
                    print("[DEBUG] Trying db.get_vendors_with_performance()")
                    df = pd.DataFrame(self.db.get_vendors_with_performance())
                elif hasattr(self.db, "get_vendors"):
                    print("[DEBUG] Trying db.get_vendors()")
                    df = pd.DataFrame(self.db.get_vendors())
            elif report_type == "Financial Summary":
                if hasattr(self.db, "get_financials"):
                    df = pd.DataFrame(self.db.get_financials())
            elif report_type == "Risk Assessment":
                if hasattr(self.db, "get_risk_data"):
                    df = pd.DataFrame(self.db.get_risk_data())
            elif report_type == "Compliance Status":
                if hasattr(self.db, "get_compliance_data"):
                    df = pd.DataFrame(self.db.get_compliance_data())
            elif report_type == "Executive Summary":
                if hasattr(self.db, "get_vendors"):
                    df = pd.DataFrame(self.db.get_vendors())
        except Exception as e:
            print(f"[DEBUG] DB method failed: {e}")
            df = pd.DataFrame()

        print(f"[DEBUG] DB returned {len(df)} rows")
        
        # If DB returned nothing, load forced files from Data layer
        if df is None or df.empty:
            print("[DEBUG] Trying forced files from Data layer...")
            df = self._load_forced_files(report_type)
            print(f"[DEBUG] Forced files returned {len(df)} rows")

        # If still empty, create sample data
        if df is None or df.empty:
            print("[DEBUG] Creating sample data as fallback")
            df = self._create_sample_data(report_type)

        # Normalize to DataFrame
        if not isinstance(df, pd.DataFrame):
            try:
                df = pd.DataFrame(df)
            except Exception:
                df = pd.DataFrame()

        return df.reset_index(drop=True)

    def _load_forced_files(self, report_type: str) -> pd.DataFrame:
        candidates = self.forced_file_map.get(report_type, []) + []
        print(f"[DEBUG] Looking for files for {report_type}: {candidates}")
        
        for path in candidates:
            try:
                if not path:
                    continue
                    
                # Check if file exists
                if not os.path.exists(path):
                    print(f"[DEBUG] File not found: {path}")
                    continue
                    
                print(f"[DEBUG] Attempting to load: {path}")
                lower = path.lower()
                
                if lower.endswith(".csv"):
                    df = pd.read_csv(path)
                elif lower.endswith(".json"):
                    df = pd.read_json(path)
                elif lower.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(path)
                else:
                    print(f"[DEBUG] Unsupported file format: {path}")
                    continue
                    
                if isinstance(df, pd.DataFrame) and not df.empty:
                    print(f"[SUCCESS] Loaded {len(df)} rows from {path}")
                    print(f"[DEBUG] Columns: {list(df.columns)}")
                    return df
                else:
                    print(f"[DEBUG] File {path} is empty or not a DataFrame")
                    
            except Exception as e:
                print(f"[ERROR] Failed to read {path}: {e}")
                continue
                
        print(f"[DEBUG] No suitable files found for {report_type}")
        return pd.DataFrame()

    def _create_sample_data(self, report_type: str) -> pd.DataFrame:
        """Create sample data when no real data is available"""
        import random
        if report_type == "Vendor Performance":
            vendors = ['TechCorp Inc', 'Global Supplies', 'Quality Parts Co', 
                       'Innovative Solutions', 'Reliable Services', 'Prime Vendors LLC']
            
            data = []
            for i, vendor in enumerate(vendors):
                data.append({
                    'Vendor Name': vendor,
                    'Contract Value USD': random.randint(50000, 200000),
                    'Performance Rating': round(random.uniform(6.0, 9.9), 1),
                    'On Time Delivery %': random.randint(85, 99),
                    'Contract Date': f'2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                    'Compliance Status': random.choice(['Compliant', 'Pending', 'Compliant']),
                    'Risk Level': random.choice(['Low', 'Medium', 'Low', 'High'])
                })
            
            return pd.DataFrame(data)
        elif report_type == "Financial Summary":
            return pd.DataFrame({
                'Metric': ['Revenue', 'Cost', 'Profit', 'ROI'],
                'Value': [1000000, 650000, 350000, 0.35],
                'Month': ['Jan', 'Jan', 'Jan', 'Jan']
            })
        # Add more sample data for other report types as needed
        return pd.DataFrame()

    def check_data_layer_files(self):
        """Check what files are available in Data layer folder"""
        import glob
        print("=== Checking Data layer folder ===")
        
        # Check Data layer directory
        data_layer_files = glob.glob("Data layer/*") + glob.glob("./Data layer/*")
        
        if not data_layer_files:
            print("No files found in Data layer folder!")
            print("Current working directory:", os.getcwd())
            print("Trying to list directory contents:")
            try:
                print(os.listdir("."))
                if os.path.exists("Data layer"):
                    print("Data layer folder exists, contents:", os.listdir("Data layer"))
                else:
                    print("Data layer folder does not exist!")
            except Exception as e:
                print(f"Error listing directory: {e}")
        else:
            print("Files found in Data layer:")
            for file in data_layer_files:
                print(f"  - {file}")
        
        return data_layer_files

    def test_data_loading(self, report_type: str = "Vendor Performance"):
        """Test data loading for a specific report type"""
        print(f"\n=== Testing data loading for {report_type} ===")
        
        # First check what files we have
        self.check_data_layer_files()
        
        # Try to load data
        df = self._get_report_data(report_type)
        
        print(f"Final result: {len(df)} rows loaded")
        if not df.empty:
            print(f"Columns: {list(df.columns)}")
            print("First few rows:")
            print(df.head(3))
        else:
            print("No data loaded!")
        
        return df

    # -------------------------
    # Heuristics to find key columns
    # -------------------------
    def _find_name_column(self, df: pd.DataFrame) -> Optional[str]:
        if df.empty:
            return None
        candidates = [c for c in df.columns if any(k in c.lower() for k in ("name", "vendor", "company"))]
        return candidates[0] if candidates else df.columns[0]

    def _find_value_column(self, df: pd.DataFrame) -> Optional[str]:
        if df.empty:
            return None
        numeric_candidates = [c for c in df.columns if any(k in c.lower() for k in ("contract", "value", "amount", "spend", "cost", "revenue", "invoice"))]
        if numeric_candidates:
            return numeric_candidates[0]
        # fallback: any numeric column
        for c in df.columns:
            try:
                pd.to_numeric(df[c].dropna().iloc[:10])
                return c
            except Exception:
                continue
        return None

    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        if df.empty:
            return None
        date_candidates = [c for c in df.columns if any(k in c.lower() for k in ("date", "month", "created", "timestamp"))]
        return date_candidates[0] if date_candidates else None

    # -------------------------
    # Chart generation utilities (matplotlib)
    # -------------------------
    def _save_bar_chart(self, df: pd.DataFrame, name_col: str, value_col: str, out_path: str):
        plt.close("all")
        if df.empty or name_col is None or value_col is None or name_col not in df.columns or value_col not in df.columns:
            fig = plt.figure(figsize=(6, 3))
            plt.text(0.5, 0.5, "No data for top vendors", ha="center", va="center")
            plt.axis("off")
            fig.savefig(out_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return out_path
        
        df2 = df[[name_col, value_col]].copy()
        df2[value_col] = pd.to_numeric(df2[value_col], errors="coerce").fillna(0)
        top = df2.sort_values(value_col, ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(top[name_col].astype(str)[::-1], top[value_col].astype(float)[::-1])
        ax.set_xlabel(value_col)
        ax.set_title("Top Vendors by " + value_col)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}" if abs(x) >= 1000 else f"{x:,.0f}"))
        plt.tight_layout()
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def _save_trend_chart(self, df: pd.DataFrame, date_col: Optional[str], value_col: str, out_path: str):
        plt.close("all")
        if df.empty or value_col is None or value_col not in df.columns:
            fig = plt.figure(figsize=(6, 3))
            plt.text(0.5, 0.5, "No trend data available", ha="center", va="center")
            plt.axis("off")
            fig.savefig(out_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return out_path

        if date_col and date_col in df.columns:
            d = df[[date_col, value_col]].dropna().copy()
            try:
                d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
                d = d.dropna(subset=[date_col])
                if d.empty:
                    raise ValueError("No valid dates")
                # aggregate monthly
                d = d.groupby(pd.Grouper(key=date_col, freq="M"))[value_col].sum().reset_index()
                fig, ax = plt.subplots(figsize=(8, 3.5))
                ax.plot(d[date_col], d[value_col], marker="o", linewidth=2)
                ax.set_title(value_col + " Trend")
                ax.set_ylabel(value_col)
                ax.grid(alpha=0.25)
                plt.tight_layout()
                fig.savefig(out_path, dpi=150, bbox_inches="tight")
                plt.close(fig)
                return out_path
            except Exception:
                pass

        # fallback: if no date col, try to plot index vs aggregated values
        try:
            tmp = df[[value_col]].copy()
            tmp[value_col] = pd.to_numeric(tmp[value_col], errors="coerce").fillna(0)
            tmp = tmp.head(24)  # up to 24 rows
            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.plot(range(len(tmp)), tmp[value_col], marker="o", linewidth=2)
            ax.set_title(value_col + " (index trend)")
            ax.grid(alpha=0.25)
            plt.tight_layout()
            fig.savefig(out_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return out_path
        except Exception:
            fig = plt.figure(figsize=(6, 3))
            plt.text(0.5, 0.5, "Unable to build trend", ha="center", va="center")
            plt.axis("off")
            fig.savefig(out_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            return out_path

    # -------------------------
    # PDF builder
    # -------------------------
    def _generate_pdf(self, report_type: str) -> str:
        df = self._get_report_data(report_type)
        name_col = self._find_name_column(df)
        value_col = self._find_value_column(df)
        date_col = self._find_date_column(df)

        # build summary
        summary = {
            "report_type": report_type,
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_records": int(len(df)),
            "columns": list(df.columns),
            "total_value": None,
            "average_value": None,
        }
        if value_col and value_col in df.columns and not df.empty:
            try:
                tmp = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
                summary["total_value"] = float(tmp.sum())
                summary["average_value"] = float(tmp.mean())
            except Exception:
                pass

        filename = f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=80, bottomMargin=60)
        story = []

        # Title + meta
        story.append(Paragraph(f"{report_type} Report", self.styles["ReportTitle"]))
        story.append(Paragraph(f"Generated on: {summary['generated_on']}", self.styles["NormalBody"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Executive Summary</b>", self.styles["Highlight"]))
        summary_lines = [f"Total records: <b>{summary['total_records']}</b>"]
        if summary["total_value"] is not None:
            summary_lines.append(f"Total {value_col}: <b>${summary['total_value']:,.0f}</b>")
            summary_lines.append(f"Average {value_col}: <b>${summary['average_value']:,.0f}</b>")
        for line in summary_lines:
            story.append(Paragraph(line, self.styles["NormalBody"]))
        story.append(Spacer(1, 12))

        # Charts
        bar_path = os.path.join(self.charts_dir, f"bar_{filename}.png")
        trend_path = os.path.join(self.charts_dir, f"trend_{filename}.png")
        self._save_bar_chart(df, name_col, value_col or "", bar_path)
        self._save_trend_chart(df, date_col, value_col or "", trend_path)

        if os.path.exists(bar_path):
            story.append(Paragraph("<b>Top Vendors</b>", self.styles["NormalBody"]))
            story.append(Spacer(1, 6))
            story.append(RLImage(bar_path, width=6.5 * inch, height=3 * inch))
            story.append(Spacer(1, 12))
        if os.path.exists(trend_path):
            story.append(Paragraph("<b>Trend</b>", self.styles["NormalBody"]))
            story.append(Spacer(1, 6))
            story.append(RLImage(trend_path, width=6.5 * inch, height=2.7 * inch))
            story.append(Spacer(1, 12))

        # Data snapshot table (limit columns)
        if not df.empty:
            show_df = df.copy().iloc[:, :8]
            table_data = [list(show_df.columns.astype(str))]
            for _, r in show_df.head(30).iterrows():
                table_data.append([str(x) for x in r.values])
            tbl = Table(table_data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f6fb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0b3d91")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), self.default_body_font),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]))
            story.append(Paragraph("<b>Data Snapshot</b>", self.styles["NormalBody"]))
            story.append(Spacer(1, 6))
            story.append(tbl)
        else:
            story.append(Paragraph("No data available to display.", self.styles["NormalBody"]))

        # Header/footer callback
        def _on_page(canvas_obj, doc_obj):
            w, h = A4
            canvas_obj.setFont(self.default_body_font, 9)
            canvas_obj.setFillColor(colors.grey)
            canvas_obj.drawString(doc_obj.leftMargin, 20, f"Generated: {summary['generated_on']}")
            canvas_obj.drawRightString(w - doc_obj.rightMargin, 20, f"Page {canvas_obj.getPageNumber()}")

        doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
        return f"✅ PDF generated: {filepath}"

    # -------------------------
    # Excel builder
    # -------------------------
    def _generate_excel(self, report_type: str) -> str:
        df = self._get_report_data(report_type)
        name_col = self._find_name_column(df)
        value_col = self._find_value_column(df)

        filename = f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)

        with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
            # write data sheet
            if not df.empty:
                df.to_excel(writer, sheet_name="Data", index=False)
            else:
                pd.DataFrame().to_excel(writer, sheet_name="Data", index=False)

            # create summary sheet
            workbook = writer.book
            summary_sheet = workbook.add_worksheet("Summary")
            bold = workbook.add_format({"bold": True})
            money = workbook.add_format({"num_format": "$#,##0"})
            summary_sheet.write("A1", "Report", bold)
            summary_sheet.write("B1", report_type)
            summary_sheet.write("A2", "Generated on", bold)
            summary_sheet.write("B2", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            summary_sheet.write("A3", "Total records", bold)
            summary_sheet.write("B3", len(df))
            if value_col and value_col in df.columns:
                tmp = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
                summary_sheet.write("A4", f"Total {value_col}", bold)
                summary_sheet.write_number("B4", float(tmp.sum()), money)
                summary_sheet.write("A5", f"Average {value_col}", bold)
                summary_sheet.write_number("B5", float(tmp.mean()), money)

            # top vendors and chart
            if not df.empty and name_col in df.columns and value_col in df.columns:
                df2 = df[[name_col, value_col]].copy()
                df2[value_col] = pd.to_numeric(df2[value_col], errors="coerce").fillna(0)
                top = df2.sort_values(value_col, ascending=False).head(10)
                top.to_excel(writer, sheet_name="TopVendors", index=False)
                worksheet = writer.sheets["TopVendors"]
                chart = workbook.add_chart({"type": "column"})
                # categories and values reference TopVendors sheet; ensure not to break when small
                chart.add_series({
                    "name": value_col,
                    "categories": ["TopVendors", 1, 0, len(top), 0],
                    "values": ["TopVendors", 1, 1, len(top), 1],
                })
                chart.set_title({"name": f"Top Vendors by {value_col}"})
                chart.set_x_axis({"name": name_col})
                chart.set_y_axis({"name": value_col, "num_format": "$#,##0"})
                worksheet.insert_chart("D2", chart, {"x_scale": 1.2, "y_scale": 1.0})

        return f"✅ Excel generated: {filepath}"

    # -------------------------
    # HTML builder
    # -------------------------
    def _generate_html(self, report_type: str) -> str:
        df = self._get_report_data(report_type)
        name_col = self._find_name_column(df)
        value_col = self._find_value_column(df)
        date_col = self._find_date_column(df)

        filename = f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(self.output_dir, filename)

        bar_path = os.path.join(self.charts_dir, f"bar_{filename}.png")
        trend_path = os.path.join(self.charts_dir, f"trend_{filename}.png")
        self._save_bar_chart(df, name_col, value_col or "", bar_path)
        self._save_trend_chart(df, date_col, value_col or "", trend_path)

        def _img_b64(path):
            if not os.path.exists(path):
                return ""
            with open(path, "rb") as f:
                return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

        parts = []
        parts.append("<!doctype html><html><head><meta charset='utf-8'><title>Report</title>")
        parts.append("<style>body{font-family:Arial,Helvetica,sans-serif;margin:20px} .summary{background:#f7fbff;padding:10px;border-left:4px solid #1f77b4} table{border-collapse:collapse;width:100%} th,td{border:1px solid #ddd;padding:8px} th{background:#f3f6fb;color:#0b3d91}</style>")
        parts.append("</head><body>")
        parts.append(f"<h1>{report_type} Report</h1>")
        parts.append(f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        parts.append("<div class='summary'>")
        parts.append(f"<p><strong>Total records:</strong> {len(df)}</p>")
        if value_col and value_col in df.columns:
            try:
                tmp = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
                parts.append(f"<p><strong>Total {value_col}:</strong> ${tmp.sum():,.0f}</p>")
                parts.append(f"<p><strong>Average {value_col}:</strong> ${tmp.mean():,.0f}</p>")
            except Exception:
                pass
        parts.append("</div>")

        bar_b64 = _img_b64(bar_path)
        trend_b64 = _img_b64(trend_path)
        if bar_b64:
            parts.append("<h2>Top Vendors</h2>")
            parts.append(f"<img src='{bar_b64}' style='max-width:100%;height:auto'/>")
        if trend_b64:
            parts.append("<h2>Trend</h2>")
            parts.append(f"<img src='{trend_b64}' style='max-width:100%;height:auto'/>")

        parts.append("<h2>Data Snapshot</h2>")
        if not df.empty:
            parts.append(df.iloc[:, :8].head(30).to_html(index=False, classes="dataframe", border=0))
        else:
            parts.append("<p>No data to display.</p>")

        parts.append("</body></html>")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))

        return f"✅ HTML generated: {filepath}"

    # -------------------------
    # Public API
    # -------------------------
    def generate_report(self, report_type: str, format_type: str) -> str:
        fmt = (format_type or "PDF").strip().upper()
        if fmt == "PDF":
            return self._generate_pdf(report_type)
        if fmt in ("EXCEL", "XLSX"):
            return self._generate_excel(report_type)
        if fmt == "HTML":
            return self._generate_html(report_type)
        return f"❌ Unsupported format: {format_type}"

    def get_generated_reports(self):
        items = []
        for fname in os.listdir(self.output_dir):
            full = os.path.join(self.output_dir, fname)
            if os.path.isfile(full):
                items.append({"name": fname, "size": os.path.getsize(full), "created": datetime.fromtimestamp(os.path.getctime(full))})
        return sorted(items, key=lambda x: x["created"], reverse=True)
    
