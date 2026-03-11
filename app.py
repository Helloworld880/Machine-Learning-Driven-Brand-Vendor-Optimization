# #!/usr/bin/env python3
# """
# app.py - Vendor Performance Dashboard (fixed)
# """

# import streamlit as st

# # MUST BE FIRST STREAMLIT COMMAND
# st.set_page_config(page_title="Vendor Performance Dashboard", page_icon="📊", layout="wide")

# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime
# import os
# import base64
# import warnings
# warnings.filterwarnings("ignore")

# # local modules (ensure these files exist in your project)
# from core_modules.auth import Authentication
# from core_modules.database import DatabaseManager
# from core_modules.analytics import AnalyticsEngine
# from core_modules.email_service import EmailService
# from core_modules.config import Config
# from core_modules.api import APIManager

# # Import ReportGenerator with lazy loading to avoid circular imports
# REPORT_GENERATOR_AVAILABLE = True
# ReportGenerator = None

# try:
#     from enhancements.report_generator import ReportGenerator as RG
#     ReportGenerator = RG
# except ImportError as e:
#     st.error(f"⚠️ Report Generator not available: {e}")
#     REPORT_GENERATOR_AVAILABLE = False
#     # Create a dummy class for fallback
#     class ReportGenerator:
#         def __init__(self, db):
#             self.db = db
#         def generate_report(self, report_type, format_type):
#             return f"❌ Report generator not available. Please check the installation."
#         def get_generated_reports(self):
#             return []

# # Other enhancements
# from enhancements.financial_analytics import FinancialAnalytics
# from enhancements.predictive_analytics import PredictiveAnalytics
# from enhancements.compliance_manager import ComplianceManager
# from enhancements.workflow_engine import WorkflowEngine
# from enhancements.benchmarking import Benchmarking
# from enhancements.vendor_collaboration import VendorCollaboration

# # -------------------------
# # Helpers
# # -------------------------
# def to_dataframe(obj):
#     """Convert various DB return shapes to pandas.DataFrame safely."""
#     if isinstance(obj, pd.DataFrame):
#         return obj.copy()
#     if obj is None:
#         return pd.DataFrame()
#     if isinstance(obj, list):
#         try:
#             return pd.DataFrame(obj)
#         except Exception:
#             return pd.DataFrame()
#     try:
#         # try to consume iterable
#         return pd.DataFrame(list(obj))
#     except Exception:
#         try:
#             return pd.DataFrame(obj)
#         except Exception:
#             return pd.DataFrame()

# def ensure_numeric_columns(df, defaults):
#     for col, default in defaults.items():
#         if col not in df.columns:
#             df[col] = default
#         else:
#             df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)
#     return df

# def safe_get_vendors(db):
#     try:
#         if db and hasattr(db, "get_vendors"):
#             res = db.get_vendors()
#             return to_dataframe(res)
#     except Exception as e:
#         print("[app] get_vendors error:", e)
#     return pd.DataFrame()

# def safe_get_vendors_with_performance(db):
#     try:
#         if db and hasattr(db, "get_vendors_with_performance"):
#             res = db.get_vendors_with_performance()
#             return to_dataframe(res)
#     except Exception as e:
#         print("[app] get_vendors_with_performance error:", e)
#     return pd.DataFrame()

# # -------------------------
# # VendorDashboard
# # -------------------------
# class VendorDashboard:
#     def __init__(self):
#         self.config = Config()
#         self.auth = Authentication()
#         self.db = DatabaseManager()
#         self.analytics = AnalyticsEngine(self.db)
#         self.email_service = EmailService()
#         self.api_manager = APIManager()
#         self.financial_analytics = FinancialAnalytics(self.db)
#         self.predictive_analytics = PredictiveAnalytics(self.db)
#         self.compliance_manager = ComplianceManager(self.db)
#         self.workflow_engine = WorkflowEngine(self.db)
#         self.benchmarking = Benchmarking(self.db)
#         self.vendor_collaboration = VendorCollaboration(self.db)

#         # Lazy initialization for ReportGenerator
#         self._report_generator = None

#         self.setup_page_styles()  # Changed from setup_page_config
#         self.initialize_session_state()

#     @property
#     def report_generator(self):
#         """Lazy loader for report generator to avoid circular imports"""
#         if self._report_generator is None:
#             if REPORT_GENERATOR_AVAILABLE and ReportGenerator is not None:
#                 try:
#                     self._report_generator = ReportGenerator(self.db)
#                 except Exception as e:
#                     print(f"[app] ReportGenerator init error: {e}")
#                     # Fallback to dummy generator
#                     self._report_generator = ReportGenerator(self.db)
#             else:
#                 self._report_generator = ReportGenerator(self.db)
#         return self._report_generator

#     def initialize_session_state(self):
#         if "selected_vendor" not in st.session_state:
#             st.session_state.selected_vendor = None
#         if "performance_threshold" not in st.session_state:
#             st.session_state.performance_threshold = 70
#         if "auto_refresh" not in st.session_state:
#             st.session_state.auto_refresh = False
#         if "selected_nav" not in st.session_state:
#             st.session_state.selected_nav = "Overview Dashboard"
#         if "user" not in st.session_state:
#             st.session_state.user = None

#     def setup_page_styles(self):
#         """Only setup styles, not page config (already done at top)"""
#         st.markdown(
#             """
#         <style>
#         .main-header {font-size: 2.1rem; color: #1f77b4; text-align: center; margin-bottom: 1rem; font-weight: 600;}
#         </style>
#         """,
#             unsafe_allow_html=True,
#         )

#     # Sidebar
#     def render_sidebar(self):
#         with st.sidebar:
#             st.title("Vendor Dashboard")
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("🔄 Refresh Data", use_container_width=True):
#                     st.rerun()
#             with col2:
#                 if st.button("🏠 Overview", use_container_width=True):
#                     st.session_state.selected_nav = "Overview Dashboard"
#                     st.rerun()

#             if st.session_state.user is None:
#                 with st.form("login_form"):
#                     username = st.text_input("Username")
#                     password = st.text_input("Password", type="password")
#                     if st.form_submit_button("Login"):
#                         user = self.auth.authenticate(username, password)
#                         if user:
#                             st.session_state.user = user
#                             st.success(f"Welcome {user.get('name', username)}!")
#                             st.rerun()
#                         else:
#                             st.error("Invalid credentials")
#             else:
#                 st.success(f"👋 {st.session_state.user.get('name','User')}")
#                 if st.button("Logout"):
#                     st.session_state.user = None
#                     st.rerun()

#             if st.session_state.user:
#                 st.divider()
#                 st.subheader("Navigation")
#                 nav_options = [
#                     "Overview Dashboard",
#                     "Vendor Performance",
#                     "Financial Analytics",
#                     "Brand & ESG Analytics",
#                     "Risk Management",
#                     "Compliance",
#                     "Reports",
#                     "Vendor Portal",
#                     "Settings",
#                 ]
#                 current_index = nav_options.index(st.session_state.get("selected_nav", nav_options[0])) if st.session_state.get("selected_nav") in nav_options else 0
#                 st.session_state.selected_nav = st.selectbox("Go to", nav_options, index=current_index)

#                 st.divider()
#                 st.subheader("Filters")
#                 time_period = st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All Time"])
#                 perf_threshold = st.slider("Performance Alert Threshold", 0, 100, st.session_state.performance_threshold)
#                 st.session_state.filters = {"time_period": time_period, "performance_threshold": perf_threshold}
#                 st.session_state.performance_threshold = perf_threshold

#     # Overview
#     def render_overview_dashboard(self):
#         st.markdown('<div class="main-header">📈 Vendor Performance Overview</div>', unsafe_allow_html=True)

#         vendors = safe_get_vendors(self.db)
#         vendors = ensure_numeric_columns(vendors, {"deliveries": 0, "on_time_pct": 0.0, "defect_rate_pct": 0.0, "contract_value": 0, "brand_score": 0.0})

#         total_vendors = len(vendors) if not vendors.empty else 0

#         if not vendors.empty:
#             avg_contract_value = vendors["contract_value"].mean() if "contract_value" in vendors.columns else 0
#             max_contract = vendors["contract_value"].max() if "contract_value" in vendors.columns else 0
#             avg_perf = (avg_contract_value / max_contract * 100) if max_contract > 0 else 75.0

#             risk_count = (vendors["risk_level"].astype(str).str.lower() == "high").sum() if "risk_level" in vendors.columns else 0
#             active_vendors = (vendors["status"].astype(str).str.lower() == "active").sum() if "status" in vendors.columns else total_vendors
#             total_contract_value = int(vendors["contract_value"].sum()) if "contract_value" in vendors.columns else 0
#         else:
#             avg_perf = 75.0
#             risk_count = 0
#             active_vendors = 0
#             total_contract_value = 0

#         c1, c2, c3, c4 = st.columns(4)
#         c1.metric("Total Vendors", total_vendors)
#         c2.metric("Active Vendors", active_vendors)
#         c3.metric("High Risk Vendors", risk_count)
#         c4.metric("Total Contract Value", f"${total_contract_value:,.0f}")

#         st.divider()
#         st.subheader("Performance Insights")

#         if not vendors.empty and "contract_value" in vendors.columns and "name" in vendors.columns:
#             top_vendors = vendors.nlargest(15, "contract_value")
#             fig_bar = px.bar(top_vendors, x="name", y="contract_value", color="contract_value", color_continuous_scale="Blues", title="Top 15 Vendors by Contract Value", labels={"contract_value": "Contract Value ($)", "name": "Vendor Name"})
#             fig_bar.update_layout(xaxis_tickangle=-45)
#             st.plotly_chart(fig_bar, use_container_width=True)

#             if "category" in vendors.columns:
#                 st.subheader("Vendor Distribution by Category")
#                 category_counts = vendors["category"].value_counts().reset_index()
#                 category_counts.columns = ["category", "count"]
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     fig_pie = px.pie(category_counts, names="category", values="count", title="Vendor Distribution by Category")
#                     st.plotly_chart(fig_pie, use_container_width=True)
#                 with col2:
#                     category_contracts = vendors.groupby("category")["contract_value"].mean().reset_index()
#                     fig_bar_cat = px.bar(category_contracts, x="category", y="contract_value", title="Average Contract Value by Category", color="contract_value", color_continuous_scale="Viridis")
#                     st.plotly_chart(fig_bar_cat, use_container_width=True)
#         else:
#             if vendors.empty:
#                 st.info("No vendor data available.")
#             else:
#                 st.warning(f"Available columns: {list(vendors.columns)}")
#                 st.dataframe(vendors.head(10), use_container_width=True)

#     # Vendor Performance
#     def render_vendor_performance(self):
#         st.markdown('<div class="main-header">📊 Vendor Performance Analysis</div>', unsafe_allow_html=True)

#         vendors_data = safe_get_vendors_with_performance(self.db)
#         if vendors_data.empty:
#             vendors_data = safe_get_vendors(self.db)

#         vendors_data = ensure_numeric_columns(vendors_data, {"deliveries": 0, "on_time_pct": 0.0, "defect_rate_pct": 0.0, "contract_value": 0, "brand_score": 0.0})

#         st.success(f"📊 Loaded {len(vendors_data)} vendor records")

#         if not vendors_data.empty:
#             with st.expander("🔍 View Data Structure"):
#                 st.write("Available columns:", list(vendors_data.columns))
#                 st.dataframe(vendors_data.head(), use_container_width=True)

#             vendor_name_col = "name" if "name" in vendors_data.columns else (vendors_data.columns[0] if len(vendors_data.columns) > 0 else None)
#             performance_col = "contract_value" if "contract_value" in vendors_data.columns else None

#             if vendor_name_col and performance_col:
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     vendor_options = vendors_data[vendor_name_col].dropna().unique().tolist()
#                     v1 = st.selectbox("Select Vendor 1", vendor_options)
#                 with col2:
#                     v2 = st.selectbox("Select Vendor 2", [v for v in vendor_options if v != v1] if v1 else vendor_options)

#                 if v1 and v2:
#                     v1_data = vendors_data[vendors_data[vendor_name_col] == v1]
#                     v2_data = vendors_data[vendors_data[vendor_name_col] == v2]
#                     if not v1_data.empty and not v2_data.empty:
#                         v1_value = float(v1_data[performance_col].iloc[0])
#                         v2_value = float(v2_data[performance_col].iloc[0])
#                         diff = v1_value - v2_value
#                         c1, c2, c3 = st.columns(3)
#                         c1.metric(v1, f"${v1_value:,.0f}")
#                         c2.metric(v2, f"${v2_value:,.0f}")
#                         c3.metric("Difference", f"${diff:,.0f}")
#                         st.divider()
#                         comparison_data = vendors_data[vendors_data[vendor_name_col].isin([v1, v2])]
#                         fig_comp = px.bar(comparison_data, x=vendor_name_col, y=performance_col, color=vendor_name_col, title="Vendor Contract Value Comparison", labels={performance_col: "Contract Value ($)", vendor_name_col: "Vendor"}, text_auto=True)
#                         st.plotly_chart(fig_comp, use_container_width=True)

#             st.subheader("📈 Contract Value Distribution")
#             if performance_col:
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     fig_hist = px.histogram(vendors_data, x=performance_col, title="Contract Value Distribution", nbins=10, labels={performance_col: "Contract Value ($)"})
#                     st.plotly_chart(fig_hist, use_container_width=True)
#                 with col2:
#                     top_vendors = vendors_data.nlargest(10, performance_col)
#                     fig_bar = px.bar(top_vendors, x=vendor_name_col, y=performance_col, title="Top 10 Vendors by Contract Value", color=performance_col, color_continuous_scale="Viridis")
#                     fig_bar.update_layout(xaxis_tickangle=-45)
#                     st.plotly_chart(fig_bar, use_container_width=True)

#             category_col = "category" if "category" in vendors_data.columns else None
#             if category_col and performance_col:
#                 st.subheader("🏷️ Analysis by Category")
#                 c1, c2 = st.columns(2)
#                 with c1:
#                     category_avg = vendors_data.groupby(category_col)[performance_col].mean().reset_index()
#                     fig_cat_avg = px.bar(category_avg, x=category_col, y=performance_col, title="Average Contract Value by Category", text_auto=True)
#                     st.plotly_chart(fig_cat_avg, use_container_width=True)
#                 with c2:
#                     category_count = vendors_data[category_col].value_counts().reset_index()
#                     category_count.columns = [category_col, "count"]
#                     fig_cat_count = px.pie(category_count, names=category_col, values="count", title="Vendor Count by Category")
#                     st.plotly_chart(fig_cat_count, use_container_width=True)

#             if "risk_level" in vendors_data.columns:
#                 st.subheader("⚠️ Risk Analysis")
#                 c1, c2 = st.columns(2)
#                 with c1:
#                     risk_counts = vendors_data["risk_level"].value_counts().reset_index()
#                     risk_counts.columns = ["risk_level", "count"]
#                     fig_risk = px.pie(risk_counts, names="risk_level", values="count", title="Risk Level Distribution")
#                     st.plotly_chart(fig_risk, use_container_width=True)
#                 with c2:
#                     if performance_col:
#                         risk_contracts = vendors_data.groupby("risk_level")[performance_col].mean().reset_index()
#                         fig_risk_contracts = px.bar(risk_contracts, x="risk_level", y=performance_col, title="Avg Contract Value by Risk Level")
#                         st.plotly_chart(fig_risk_contracts, use_container_width=True)

#             st.subheader("📋 Vendor Details")
#             col1, col2, col3 = st.columns(3)
#             filtered_data = vendors_data.copy()
#             with col1:
#                 if vendor_name_col:
#                     selected_vendors = st.multiselect("Filter by Vendor", vendors_data[vendor_name_col].unique().tolist())
#                     if selected_vendors:
#                         filtered_data = filtered_data[filtered_data[vendor_name_col].isin(selected_vendors)]
#             with col2:
#                 if category_col:
#                     selected_categories = st.multiselect("Filter by Category", vendors_data[category_col].unique().tolist())
#                     if selected_categories:
#                         filtered_data = filtered_data[filtered_data[category_col].isin(selected_categories)]
#             with col3:
#                 if "risk_level" in vendors_data.columns:
#                     selected_risks = st.multiselect("Filter by Risk Level", vendors_data["risk_level"].unique().tolist())
#                     if selected_risks:
#                         filtered_data = filtered_data[filtered_data["risk_level"].isin(selected_risks)]

#             if performance_col and not vendors_data.empty:
#                 try:
#                     min_val = int(vendors_data[performance_col].min())
#                     max_val = int(vendors_data[performance_col].max())
#                     value_range = st.slider("Contract Value Range", min_value=min_val, max_value=max_val, value=(min_val, max_val))
#                     filtered_data = filtered_data[(filtered_data[performance_col] >= value_range[0]) & (filtered_data[performance_col] <= value_range[1])]
#                 except Exception:
#                     pass

#             st.dataframe(filtered_data, use_container_width=True)
#             csv_bytes = filtered_data.to_csv(index=False).encode("utf-8")
#             st.download_button(label="📥 Download Filtered Data as CSV", data=csv_bytes, file_name="vendor_analysis.csv", mime="text/csv")
#         else:
#             st.info("No vendor performance data available.")

#     # -------------------------------------------------
#     # FINANCIAL ANALYTICS
#     # -------------------------------------------------
#     def render_financial_analytics(self):
#         st.markdown('<div class="main-header">💰 Financial Analytics</div>', unsafe_allow_html=True)
        
#         # Create comprehensive financial data
#         financial_data = pd.DataFrame({
#             'category': ['IT Services', 'Logistics', 'Manufacturing', 'Consulting', 'Raw Materials', 'Marketing', 'Facilities'],
#             'cost_savings': [45000, 32000, 28000, 35000, 22000, 18000, 15000],
#             'total_spend': [250000, 180000, 320000, 120000, 280000, 90000, 110000],
#             'vendor_count': [12, 8, 15, 6, 9, 7, 5],
#             'savings_rate': [18.0, 17.8, 8.8, 29.2, 7.9, 20.0, 13.6],
#             'qtr': ['Q1', 'Q1', 'Q1', 'Q1', 'Q1', 'Q1', 'Q1']
#         })
        
#         st.success(f"💰 Financial data loaded with {len(financial_data)} categories")
        
#         # Financial Metrics
#         total_savings = financial_data['cost_savings'].sum()
#         total_spend = financial_data['total_spend'].sum()
#         overall_savings_rate = (total_savings / total_spend * 100)
        
#         col1, col2, col3, col4 = st.columns(4)
#         col1.metric("Total Savings", f"${total_savings:,.0f}")
#         col2.metric("Total Spend", f"${total_spend:,.0f}")
#         col3.metric("Savings Rate", f"{overall_savings_rate:.1f}%")
#         col4.metric("Categories", len(financial_data))
        
#         st.divider()
        
#         # Savings Analysis
#         st.subheader("💵 Savings Analysis")
#         col1, col2 = st.columns(2)
        
#         with col1:
#             fig_bar = px.bar(financial_data, x="category", y="cost_savings",
#                            title="Cost Savings by Category",
#                            color="cost_savings", color_continuous_scale="Viridis",
#                            text_auto=True)
#             fig_bar.update_layout(xaxis_tickangle=-45)
#             st.plotly_chart(fig_bar, use_container_width=True)
        
#         with col2:
#             fig_pie = px.pie(financial_data, names="category", values="cost_savings",
#                            title="Savings Distribution by Category",
#                            hole=0.4)
#             st.plotly_chart(fig_pie, use_container_width=True)
        
#         # Savings Rate Analysis
#         st.subheader("📊 Savings Rate Performance")
#         fig_rate = px.bar(financial_data, x="category", y="savings_rate",
#                          title="Savings Rate by Category (%)",
#                          color="savings_rate", color_continuous_scale="RdYlGn",
#                          text_auto=True)
#         st.plotly_chart(fig_rate, use_container_width=True)
        
#         # Financial Data Table
#         st.subheader("📋 Financial Data Details")
#         st.dataframe(financial_data, use_container_width=True)

#     # -------------------------------------------------
#     # BRAND & ESG ANALYTICS
#     # -------------------------------------------------
#     def render_brand_esg_analytics(self):
#         st.markdown('<div class="main-header">🌱 Brand & ESG Analytics</div>', unsafe_allow_html=True)
        
#         # Create comprehensive brand and ESG data
#         brand_data = pd.DataFrame({
#             'brand_name': ['EcoTech Solutions', 'Green Logistics Inc', 'Sustainable Manufacturing Co', 
#                           'Ethical Consulting Group', 'Clean Energy Partners', 'Social Impact Corp',
#                           'Environmental Services Ltd', 'Carbon Neutral Industries'],
#             'sustainability_score': [88, 92, 85, 79, 95, 82, 76, 89],
#             'social_impact_score': [85, 78, 82, 91, 87, 94, 79, 83],
#             'governance_score': [90, 85, 88, 92, 84, 89, 81, 86],
#             'environmental_score': [92, 89, 83, 75, 96, 80, 78, 91],
#             'overall_esg_score': [88.8, 86.0, 84.5, 84.3, 90.5, 86.3, 78.5, 87.3],
#             'carbon_footprint': [120, 180, 320, 95, 65, 110, 280, 150],
#             'renewable_energy_pct': [85, 65, 45, 90, 95, 75, 35, 70]
#         })

#         st.success(f"🌱 ESG data loaded for {len(brand_data)} brands")
        
#         # ESG Metrics Overview
#         st.subheader("📊 ESG Performance Overview")
        
#         col1, col2, col3, col4 = st.columns(4)
#         col1.metric("Avg Sustainability", f"{brand_data['sustainability_score'].mean():.1f}")
#         col2.metric("Avg Social Impact", f"{brand_data['social_impact_score'].mean():.1f}")
#         col3.metric("Avg Governance", f"{brand_data['governance_score'].mean():.1f}")
#         col4.metric("Avg Overall ESG", f"{brand_data['overall_esg_score'].mean():.1f}")
        
#         st.divider()
        
#         # ESG Scores Visualization
#         col1, col2 = st.columns(2)
        
#         with col1:
#             fig_bar = px.bar(brand_data, x="brand_name", y="overall_esg_score",
#                            color="overall_esg_score", color_continuous_scale="Greens",
#                            title="Overall ESG Scores by Brand", text_auto=True)
#             fig_bar.update_layout(xaxis_tickangle=-45)
#             st.plotly_chart(fig_bar, use_container_width=True)
        
#         with col2:
#             # Radar chart for top brand
#             top_brand = brand_data.nlargest(1, 'overall_esg_score').iloc[0]
#             radar_categories = ['sustainability_score', 'social_impact_score', 'governance_score', 'environmental_score']
            
#             fig_radar = go.Figure()
#             fig_radar.add_trace(go.Scatterpolar(
#                 r=[top_brand[col] for col in radar_categories],
#                 theta=[col.replace('_score', '').title() for col in radar_categories],
#                 fill='toself',
#                 name=top_brand['brand_name']
#             ))
#             fig_radar.update_layout(
#                 polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
#                 title=f"ESG Radar - {top_brand['brand_name']} (Top Performer)"
#             )
#             st.plotly_chart(fig_radar, use_container_width=True)
        
#         # ESG Components Comparison
#         st.subheader("📈 ESG Components Comparison")
#         esg_components = brand_data.melt(id_vars=['brand_name'], 
#                                        value_vars=['sustainability_score', 'social_impact_score', 'governance_score'],
#                                        var_name='ESG Component', value_name='Score')
        
#         fig_components = px.bar(esg_components, x="brand_name", y="Score", color="ESG Component",
#                               title="ESG Components Comparison", barmode="group")
#         fig_components.update_layout(xaxis_tickangle=-45)
#         st.plotly_chart(fig_components, use_container_width=True)
        
#         # Brand Data Table
#         st.subheader("📋 Brand & ESG Data Details")
#         st.dataframe(brand_data, use_container_width=True)

#     # -------------------------------------------------
#     # RISK MANAGEMENT
#     # -------------------------------------------------
#     def render_risk_management(self):
#         st.markdown('<div class="main-header">⚠️ Risk Management</div>', unsafe_allow_html=True)
        
#         st.info("🚧 Risk Management module is under development")
        
#         # Sample risk data
#         risk_data = pd.DataFrame({
#             'vendor_name': [f'Vendor {i}' for i in range(1, 16)],
#             'risk_level': np.random.choice(['Low', 'Medium', 'High', 'Critical'], 15, p=[0.5, 0.3, 0.15, 0.05]),
#             'risk_score': np.random.randint(20, 95, 15),
#             'last_assessment': pd.date_range('2024-01-01', periods=15, freq='D'),
#             'mitigation_status': np.random.choice(['Not Started', 'In Progress', 'Completed', 'Monitoring'], 15),
#             'financial_risk': np.random.randint(1, 10, 15),
#             'operational_risk': np.random.randint(1, 10, 15),
#             'compliance_risk': np.random.randint(1, 10, 15)
#         })
        
#         st.subheader("Risk Overview")
#         col1, col2, col3, col4 = st.columns(4)
#         col1.metric("Total Vendors", len(risk_data))
#         col2.metric("High Risk", (risk_data['risk_level'] == 'High').sum())
#         col3.metric("Critical Risk", (risk_data['risk_level'] == 'Critical').sum())
#         col4.metric("Avg Risk Score", f"{risk_data['risk_score'].mean():.1f}")
        
#         # Risk Distribution
#         st.subheader("Risk Distribution")
#         fig_risk = px.pie(risk_data, names='risk_level', title='Vendor Risk Level Distribution')
#         st.plotly_chart(fig_risk, use_container_width=True)
        
#         # Risk Data Table
#         st.subheader("Risk Assessment Details")
#         st.dataframe(risk_data, use_container_width=True)

#     # -------------------------------------------------
#     # COMPLIANCE
#     # -------------------------------------------------
#     def render_compliance(self):
#         st.markdown('<div class="main-header">📋 Compliance Management</div>', unsafe_allow_html=True)
        
#         st.info("🚧 Compliance module is under development")
        
#         # Sample compliance data
#         compliance_data = pd.DataFrame({
#             'vendor_name': [f'Vendor {i}' for i in range(1, 12)],
#             'compliance_status': np.random.choice(['Compliant', 'Non-Compliant', 'Under Review'], 11),
#             'last_audit': pd.date_range('2024-01-01', periods=11, freq='M'),
#             'audit_score': np.random.randint(60, 100, 11),
#             'certifications': ['ISO 9001, ISO 14001', 'ISO 9001', 'SOC 2', 'ISO 27001', 'HIPAA', 
#                               'ISO 9001, ISO 14001', 'SOC 2, ISO 27001', 'ISO 9001', 'HIPAA, SOC 2', 
#                               'ISO 14001', 'ISO 9001, SOC 2'],
#             'next_audit_due': pd.date_range('2024-07-01', periods=11, freq='M')
#         })
        
#         st.subheader("Compliance Overview")
#         col1, col2, col3, col4 = st.columns(4)
#         col1.metric("Total Vendors", len(compliance_data))
#         col2.metric("Compliant", (compliance_data['compliance_status'] == 'Compliant').sum())
#         col3.metric("Non-Compliant", (compliance_data['compliance_status'] == 'Non-Compliant').sum())
#         col4.metric("Avg Audit Score", f"{compliance_data['audit_score'].mean():.1f}")
        
#         # Compliance Status
#         st.subheader("Compliance Status")
#         fig_compliance = px.bar(compliance_data, x='vendor_name', y='audit_score', 
#                               color='compliance_status', title='Vendor Compliance Status')
#         st.plotly_chart(fig_compliance, use_container_width=True)
        
#         # Compliance Data Table
#         st.subheader("Compliance Details")
#         st.dataframe(compliance_data, use_container_width=True)

#     # -------------------------------------------------
#     # REPORTS
#     # -------------------------------------------------
#     def render_reports(self):
#         st.markdown('<div class="main-header">📄 Reports & Analytics</div>', unsafe_allow_html=True)

#         # Show warning if report generator is not available
#         if not REPORT_GENERATOR_AVAILABLE:
#             st.error("""
#             ⚠️ **Report Generator is not available!**
            
#             Please make sure:
#             1. The `enhancements/report_generator.py` file exists
#             2. All required dependencies are installed: `pip install pandas matplotlib jinja2 reportlab xlsxwriter`
#             3. The file structure is correct
#             """)
#             return

#         st.subheader("Generate Reports")

#         col1, col2 = st.columns(2)

#         with col1:
#             report_type = st.selectbox(
#                 "Select Report Type",
#                 [
#                     "Vendor Performance",
#                     "Financial Summary",
#                     "Risk Assessment",
#                     "Compliance Status",
#                     "Executive Summary",
#                 ],
#             )

#         with col2:
#             format_type = st.selectbox(
#                 "Export Format",
#                 ["PDF", "Excel", "HTML"],
#             )

#         # Generate Report Button
#         generate = st.button("📊 Generate Report", type="primary", use_container_width=True)

#         if generate:
#             with st.spinner("Generating report... please wait ⏳"):
#                 result = self.report_generator.generate_report(report_type, format_type)

#                 # Check if report generated successfully
#                 if "✅" in result:
#                     filepath = result.split(":")[-1].strip()

#                     st.success(f"✅ {report_type} report generated successfully!")
#                     st.markdown(f"**📁 Saved at:** `{filepath}`")

#                     # Show actual download button
#                     try:
#                         with open(filepath, "rb") as f:
#                             file_bytes = f.read()

#                             # Display PDF preview if PDF selected
#                             if format_type == "PDF":
#                                 st.download_button(
#                                     label="⬇️ Download PDF Report",
#                                     data=file_bytes,
#                                     file_name=os.path.basename(filepath),
#                                     mime="application/pdf",
#                                 )

#                                 # Preview PDF in browser window
#                                 st.markdown(
#                                     f'<iframe src="{filepath}" width="100%" height="700px" type="application/pdf"></iframe>',
#                                     unsafe_allow_html=True,
#                                 )

#                             elif format_type == "Excel":
#                                 st.download_button(
#                                     label="⬇️ Download Excel Report",
#                                     data=file_bytes,
#                                     file_name=os.path.basename(filepath),
#                                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                                 )

#                             elif format_type == "HTML":
#                                 st.download_button(
#                                     label="⬇️ Download HTML Report",
#                                     data=file_bytes,
#                                     file_name=os.path.basename(filepath),
#                                     mime="text/html",
#                                 )
#                     except Exception as e:
#                         st.error(f"Error accessing generated file: {e}")
#                 else:
#                     st.error(result)

#         # Recently generated reports
#         st.divider()
#         st.subheader("Recent Reports")

#         reports = self.report_generator.get_generated_reports()
#         if reports:
#             df = pd.DataFrame(reports)
#             st.dataframe(df[["name", "size", "created"]], use_container_width=True)
#         else:
#             st.info("No reports generated yet.")

#     # -------------------------------------------------
#     # VENDOR PORTAL
#     # -------------------------------------------------
#     def render_vendor_portal(self):
#         st.markdown('<div class="main-header">🏢 Vendor Portal</div>', unsafe_allow_html=True)
        
#         st.info("🚧 Vendor Portal module is under development")
        
#         # Vendor information
#         st.subheader("Vendor Self-Service Portal")
        
#         tab1, tab2, tab3 = st.tabs(["📋 Profile Management", "📊 Performance", "📝 Documents"])
        
#         with tab1:
#             st.subheader("Vendor Profile")
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.text_input("Company Name", "Vendor Corporation")
#                 st.text_input("Contact Person", "John Smith")
#                 st.text_input("Email", "john@vendorcorp.com")
#                 st.text_input("Phone", "+1-555-0123")
            
#             with col2:
#                 st.text_area("Address", "123 Business Ave, Suite 100\nNew York, NY 10001")
#                 st.selectbox("Business Category", ["IT Services", "Logistics", "Manufacturing", "Consulting"])
#                 st.text_input("Tax ID", "12-3456789")
            
#             if st.button("Update Profile"):
#                 st.success("Profile updated successfully!")
        
#         with tab2:
#             st.subheader("Performance Metrics")
            
#             # Sample performance data
#             perf_metrics = pd.DataFrame({
#                 'Metric': ['Quality Score', 'Delivery Performance', 'Cost Efficiency', 'Communication', 'Overall Rating'],
#                 'Score': [88, 92, 85, 90, 89],
#                 'Industry Average': [82, 85, 80, 83, 82],
#                 'Trend': ['↗️ Improving', '→ Stable', '↗️ Improving', '→ Stable', '↗️ Improving']
#             })
            
#             st.dataframe(perf_metrics, use_container_width=True)
            
#             # Performance chart
#             fig = px.bar(perf_metrics, x='Metric', y=['Score', 'Industry Average'], 
#                         barmode='group', title='Performance vs Industry Average')
#             st.plotly_chart(fig, use_container_width=True)
        
#         with tab3:
#             st.subheader("Document Management")
            
#             documents = pd.DataFrame({
#                 'Document': ['Certificate of Insurance', 'W-9 Form', 'Quality Certifications', 'Compliance Documents'],
#                 'Status': ['✅ Approved', '✅ Approved', '🔄 Under Review', '✅ Approved'],
#                 'Last Updated': ['2024-02-15', '2024-01-20', '2024-03-01', '2024-02-28'],
#                 'Action': ['View/Download', 'View/Download', 'View/Download', 'View/Download']
#             })
            
#             st.dataframe(documents, use_container_width=True)
            
#             st.file_uploader("Upload New Document", type=['pdf', 'doc', 'docx'])

#     # -------------------------------------------------
#     # SETTINGS
#     # -------------------------------------------------
#     def render_settings(self):
#         st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)
        
#         st.info("🚧 Settings module is under development")
        
#         tab1, tab2, tab3 = st.tabs(["User Preferences", "System Settings", "Data Management"])
        
#         with tab1:
#             st.subheader("User Preferences")
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.selectbox("Theme", ["Light", "Dark", "Auto"])
#                 st.selectbox("Language", ["English", "Spanish", "French", "German"])
#                 st.slider("Dashboard Refresh Rate (minutes)", 1, 60, 5)
            
#             with col2:
#                 st.multiselect("Default Dashboard Views", 
#                               ["Overview", "Performance", "Financial", "Risk", "Compliance"])
#                 st.checkbox("Email Notifications", value=True)
#                 st.checkbox("Desktop Notifications", value=False)
            
#             if st.button("Save Preferences"):
#                 st.success("Preferences saved successfully!")
        
#         with tab2:
#             st.subheader("System Configuration")
            
#             st.number_input("Performance Threshold (%)", 0, 100, 70)
#             st.number_input("Risk Threshold (%)", 0, 100, 80)
#             st.number_input("Auto-Archive Period (days)", 30, 365, 90)
            
#             st.text_area("Email Templates", "Default email template content...", height=150)
            
#             if st.button("Update System Settings"):
#                 st.success("System settings updated!")
        
#         with tab3:
#             st.subheader("Data Management")
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.button("🔄 Refresh All Data", use_container_width=True)
#                 st.button("📤 Export All Data", use_container_width=True)
#                 st.button("🧹 Clear Cache", use_container_width=True)
            
#             with col2:
#                 st.button("🔍 Data Quality Check", use_container_width=True)
#                 st.button("📊 Generate Data Report", use_container_width=True)
#                 st.button("🗑️ Archive Old Data", use_container_width=True)
            
#             st.warning("⚠️ These actions may affect system performance")

#     # -------------------------------------------------
#     # MAIN RUN
#     # -------------------------------------------------
#     def run(self):
#         self.render_sidebar()
#         if st.session_state.user is None:
#             st.warning("Please login to access the dashboard.")
#             return

#         nav_map = {
#             "Overview Dashboard": self.render_overview_dashboard,
#             "Vendor Performance": self.render_vendor_performance,
#             "Financial Analytics": self.render_financial_analytics,
#             "Brand & ESG Analytics": self.render_brand_esg_analytics,
#             "Risk Management": self.render_risk_management,
#             "Compliance": self.render_compliance,
#             "Reports": self.render_reports,
#             "Vendor Portal": self.render_vendor_portal,
#             "Settings": self.render_settings
#         }
#         selected = st.session_state.get("selected_nav", "Overview Dashboard")
#         nav_map.get(selected, self.render_overview_dashboard)()


# # -------------------------------------------------
# # APP ENTRY POINT
# # -------------------------------------------------
# if __name__ == "__main__":
#     dashboard = VendorDashboard()
#     dashboard.run()



import streamlit as st

from api import vendors

st.set_page_config(
    page_title="ML Vendor Optimization Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# ── Local modules ────────────────────────────────────────────────────────────
from core_modules.auth import Authentication
from core_modules.database import DatabaseManager
from core_modules.analytics import AnalyticsEngine
from core_modules.config import Config

# ML Engine (lazy-loaded)
_ML_AVAILABLE = False
MLEngine = None
try:
    from enhancements.ml_engine import MLEngine as _MLEngine
    MLEngine = _MLEngine
    _ML_AVAILABLE = True
except ImportError as e:
    st.warning(f"ML engine not available: {e}. Install scikit-learn.")

# Report generator (lazy-loaded)
_REPORT_AVAILABLE = False
ReportGenerator = None
try:
    from enhancements.report_generator import ReportGenerator as _RG
    ReportGenerator = _RG
    _REPORT_AVAILABLE = True
except ImportError:
    pass


# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
def inject_styles():
    st.markdown("""
    <style>

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #1F3C88 !important;
    }

    /* Login input text color fix */
    input[type="text"], input[type="password"] {
        background-color: white !important;
        color: black !important;
        border-radius: 8px !important;
        border: 1px solid #c7d2fe !important;
        padding: 8px !important;
    }

    /* Fix label color */
    label {
        color: black !important;
        font-weight: 500;
    }

    /* Login button */
    button[kind="primary"] {
        background: linear-gradient(135deg,#2563eb,#4f46e5) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
    }

    
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def to_df(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    if obj is None:
        return pd.DataFrame()
    try:
        return pd.DataFrame(list(obj))
    except Exception:
        return pd.DataFrame()


def fmt_currency(val):
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"


def risk_color(level: str) -> str:
    return {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}.get(level, "#6b7280")


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD CLASS
# ─────────────────────────────────────────────────────────────────────────────
class VendorDashboard:
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.auth = Authentication(self.db)
        self.analytics = AnalyticsEngine(self.db)
        self._ml: object = None
        self._report_gen: object = None
        self._init_session()

    # ── Lazy ML ──────────────────────────────────────────────────────────────
    @property
    def ml(self):
        if self._ml is None and _ML_AVAILABLE and MLEngine:
            with st.spinner("🤖 Loading ML models…"):
                self._ml = MLEngine(self.db)
        return self._ml

    @property
    def report_gen(self):
        if self._report_gen is None and _REPORT_AVAILABLE and ReportGenerator:
            self._report_gen = ReportGenerator(self.db)
        return self._report_gen

    # ── Session ──────────────────────────────────────────────────────────────
    def _init_session(self):
        defaults = {
            "user": None,
            "selected_nav": "🏠 Overview",
            "perf_threshold": 70,
            "filters": {},
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    # ─────────────────────────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────────────────────────
    def render_sidebar(self):
        with st.sidebar:
            st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
            st.title("Vendor AI Platform")
            st.caption(f"v{self.config.APP_VERSION}")
            st.divider()

            # ── Login / logout ──
            if st.session_state.user is None:
                st.subheader("🔐 Login")
                with st.form("login_form", clear_on_submit=False):
                    uname = st.text_input("Username", placeholder="admin")
                    pwd = st.text_input("Password", type="password", placeholder="admin123")
                    if st.form_submit_button("Login", use_container_width=True):
                        user = self.auth.authenticate(uname, pwd)
                        if user:
                            st.session_state.user = user
                            st.success(f"Welcome, {user['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                st.info("Demo: admin / admin123")
                return

            user = st.session_state.user
            st.success(f"👋 {user['name']}")
            st.caption(f"Role: **{user['role'].upper()}**")
            if st.button("Logout", use_container_width=True):
                st.session_state.user = None
                st.rerun()

            st.divider()
            st.subheader("📌 Navigation")
            nav_options = [
                "🏠 Overview",
                "📊 Vendor Performance",
                "💰 Financial Analytics",
                "🌱 Brand & ESG",
                "⚠️ Risk Management",
                "📋 Compliance",
                "🤖 ML Predictions",
                "📄 Reports",
                "🏢 Vendor Portal",
                "⚙️ Settings",
            ]
            st.session_state.selected_nav = st.selectbox(
                "Go to", nav_options,
                index=nav_options.index(st.session_state.selected_nav)
                if st.session_state.selected_nav in nav_options else 0,
            )

            st.divider()
            st.subheader("🔧 Filters")
            st.session_state.perf_threshold = st.slider(
                "Performance Threshold", 0, 100, st.session_state.perf_threshold)
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. OVERVIEW
    # ─────────────────────────────────────────────────────────────────────────
    def render_overview(self):
        st.markdown('<div class="main-header">🏠 Vendor Performance Overview</div>',
                unsafe_allow_html=True)

        vendors = to_df(self.db.get_vendors())
        vendors_perf = to_df(self.db.get_vendors_with_performance())
        financial = to_df(self.db.get_financial_data())

        # ── KPI Calculations ─────────────────────────────
        total_vendors = len(vendors)

        active_vendors = 0
        if not vendors.empty and "status" in vendors.columns:
            active_vendors = (vendors["status"].str.lower() == "active").sum()

        avg_performance = 0
        if not vendors_perf.empty and "avg_performance" in vendors_perf.columns:
            avg_performance = vendors_perf["avg_performance"].mean()

        high_risk = 0
        if not vendors.empty and "risk_level" in vendors.columns:
            high_risk = (vendors["risk_level"].str.lower() == "high").sum()

        total_contract_value = 0
        if not vendors.empty and "contract_value" in vendors.columns:
            total_contract_value = vendors["contract_value"].sum()

        total_cost_savings = 0
        if not financial.empty and "cost_savings" in financial.columns:
            total_cost_savings = financial["cost_savings"].sum()

        # ── KPI Display ─────────────────────────────────
        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric("Total Vendors", total_vendors)
        c2.metric("Active Vendors", active_vendors)
        c3.metric("Avg Performance", f"{avg_performance:.1f}%")
        c4.metric("High Risk Vendors", high_risk)
        c5.metric("Total Contract Value", fmt_currency(total_contract_value))
        c6.metric("Total Cost Savings", fmt_currency(total_cost_savings))

        st.divider()

        # ── Charts ──────────────────────────────────────
        vendors = vendors_perf

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top Vendors by Contract Value")
            if not vendors.empty:
                top = vendors.nlargest(10, "contract_value")
                fig = px.bar(
                    top,
                    x="contract_value",
                    y="name",
                    orientation="h",
                    color="risk_level",
                    color_discrete_map={
                        "High": "#ef4444",
                        "Medium": "#f59e0b",
                        "Low": "#22c55e",
                    },
                    labels={"contract_value": "Contract Value ($)", "name": ""},
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No vendor data available.")

        with col2:
            st.subheader("Performance Trend")

            trend = to_df(self.db.get_performance_trends())

            if not trend.empty:
                trend["metric_date"] = pd.to_datetime(trend["metric_date"])

                fig = px.line(
                    trend,
                    x="metric_date",
                    y="avg_score",
                    markers=True,
                    labels={
                        "metric_date": "Date",
                        "avg_score": "Average Score",
                    },
                )

                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No performance trend data.")

        # ─────────────────────────────────────────────────────────────────────────
        # 2. VENDOR PERFORMANCE
        # ─────────────────────────────────────────────────────────────────────────
    def render_vendor_performance(self):
            st.markdown('<div class="main-header">📊 Vendor Performance Analysis</div>',
                        unsafe_allow_html=True)

            vendors = to_df(self.db.get_vendors_with_performance())
            if vendors.empty:
                st.warning("No performance data found.")
                return

            # Filter bar
            with st.expander("🔎 Filters", expanded=True):
                fc1, fc2, fc3 = st.columns(3)
                cats = ["All"] + sorted(vendors["category"].dropna().unique().tolist())
                risks = ["All", "High", "Medium", "Low"]
                sel_cat = fc1.selectbox("Category", cats)
                sel_risk = fc2.selectbox("Risk Level", risks)
                min_cv, max_cv = int(vendors["contract_value"].min()), int(vendors["contract_value"].max())
                cv_range = fc3.slider("Contract Value ($)", min_cv, max_cv, (min_cv, max_cv), step=5000)

            filt = vendors.copy()
            if sel_cat != "All":
                filt = filt[filt["category"] == sel_cat]
            if sel_risk != "All":
                filt = filt[filt["risk_level"] == sel_risk]
            filt = filt[(filt["contract_value"] >= cv_range[0]) & (filt["contract_value"] <= cv_range[1])]

            st.success(f"Showing **{len(filt)}** vendors")

            # KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Avg Performance", f"{filt['avg_performance'].mean():.1f}%" if "avg_performance" in filt else "—")
            k2.metric("Avg On-Time %", f"{filt['avg_on_time'].mean():.1f}%" if "avg_on_time" in filt else "—")
            k3.metric("Avg Defect Rate", f"{filt['avg_defect_rate'].mean():.2f}%" if "avg_defect_rate" in filt else "—")
            k4.metric("Avg Quality Score", f"{filt['avg_quality'].mean():.1f}%" if "avg_quality" in filt else "—")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                fig = px.scatter(filt, x="avg_on_time", y="avg_quality",
                                color="risk_level", size="contract_value",
                                hover_name="name", hover_data=["category"],
                                color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                                title="On-Time vs Quality Score (bubble = contract value)",
                                labels={"avg_on_time": "On-Time Delivery (%)", "avg_quality": "Quality Score (%)"})
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.box(filt, x="category", y="avg_performance",
                            color="category", title="Performance Distribution by Category",
                            labels={"avg_performance": "Performance Score (%)"})
                fig.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)

            # Heatmap
            st.subheader("📊 Vendor Metrics Heatmap")
            heat_cols = [c for c in ["avg_performance", "avg_on_time", "avg_quality", "avg_defect_rate", "contract_value"]
                        if c in filt.columns]
            if len(heat_cols) >= 2 and not filt.empty:
                heat_data = filt[["name"] + heat_cols].set_index("name")[heat_cols]
                heat_norm = (heat_data - heat_data.min()) / (heat_data.max() - heat_data.min() + 1e-9)
                fig = go.Figure(data=go.Heatmap(
                    z=heat_norm.values, x=heat_cols, y=heat_norm.index.tolist(),
                    colorscale="RdYlGn", text=heat_data.values.round(1),
                    texttemplate="%{text}", textfont={"size": 9},
                ))
                fig.update_layout(height=max(300, len(filt) * 22), yaxis_autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)

            # Vendor comparison
            st.subheader("🔄 Head-to-Head Vendor Comparison")
            v_options = filt["name"].dropna().unique().tolist()
            vc1, vc2 = st.columns(2)
            sel_v1 = vc1.selectbox("Vendor A", v_options, key="va")
            sel_v2 = vc2.selectbox("Vendor B", [v for v in v_options if v != sel_v1], key="vb")
            if sel_v1 and sel_v2:
                r1 = filt[filt["name"] == sel_v1].iloc[0]
                r2 = filt[filt["name"] == sel_v2].iloc[0]
                comp_metrics = ["avg_performance", "avg_on_time", "avg_quality"]
                fig = go.Figure()
                fig.add_trace(go.Bar(name=sel_v1, x=comp_metrics,
                                    y=[r1.get(m, 0) for m in comp_metrics], marker_color="#1f3c88"))
                fig.add_trace(go.Bar(name=sel_v2, x=comp_metrics,
                                    y=[r2.get(m, 0) for m in comp_metrics], marker_color="#f59e0b"))
                fig.update_layout(barmode="group", title="Performance Comparison")
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Vendor Table")
            st.dataframe(filt.round(2), use_container_width=True)
            st.download_button("📥 Download CSV", filt.to_csv(index=False).encode(),
                            "vendor_performance.csv", "text/csv")

        # ─────────────────────────────────────────────────────────────────────────
        # 3. FINANCIAL ANALYTICS
        # ─────────────────────────────────────────────────────────────────────────
    def render_financial_analytics(self):
            st.markdown('<div class="main-header">💰 Financial Analytics</div>',
                        unsafe_allow_html=True)

            fin_summary = to_df(self.db.get_financial_summary())
            fin_detail = to_df(self.db.get_financial_data())

            if fin_summary.empty:
                st.warning("No financial data found.")
                return

            # KPIs
            total_spend = fin_summary["total_spend"].sum()
            total_savings = fin_summary["cost_savings"].sum()
            savings_rate = (total_savings / total_spend * 100) if total_spend > 0 else 0
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Spend",         fmt_currency(total_spend))
            k2.metric("Total Cost Savings",   fmt_currency(total_savings))
            k3.metric("Overall Savings Rate", f"{savings_rate:.1f}%")
            k4.metric("Categories",           len(fin_summary))

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                fin_summary["savings_rate"] = (fin_summary["cost_savings"] / fin_summary["total_spend"] * 100).round(1)
                fig = px.bar(fin_summary, x="category", y="total_spend",
                            color="savings_rate", color_continuous_scale="RdYlGn",
                            text="savings_rate", title="Total Spend & Savings Rate by Category",
                            labels={"total_spend": "Total Spend ($)", "savings_rate": "Savings %"})
                fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
                fig.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.pie(fin_summary, names="category", values="cost_savings",
                            hole=0.4, title="Cost Savings Distribution by Category")
                st.plotly_chart(fig, use_container_width=True)

            # Trend over periods
            if not fin_detail.empty and "period" in fin_detail.columns:
                st.subheader("📈 Spend vs Savings Trend by Quarter")
                period_agg = fin_detail.groupby("period").agg(
                    total_spend=("total_spend", "sum"),
                    cost_savings=("cost_savings", "sum")
                ).reset_index().sort_values("period")
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(name="Total Spend", x=period_agg["period"],
                                    y=period_agg["total_spend"], marker_color="#93c5fd"), secondary_y=False)
                fig.add_trace(go.Scatter(name="Cost Savings", x=period_agg["period"],
                                        y=period_agg["cost_savings"], mode="lines+markers",
                                        line=dict(color="#22c55e", width=2)), secondary_y=True)
                fig.update_layout(title="Quarterly Spend vs Savings", height=380)
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Financial Details by Vendor")
            st.dataframe(fin_detail.round(2), use_container_width=True)
            st.download_button("📥 Download CSV", fin_detail.to_csv(index=False).encode(),
                            "financial_data.csv", "text/csv")

        # ─────────────────────────────────────────────────────────────────────────
        # 4. BRAND & ESG
        # ─────────────────────────────────────────────────────────────────────────
    def render_brand_esg(self):
            st.markdown('<div class="main-header">🌱 Brand & ESG Analytics</div>',
                        unsafe_allow_html=True)

            brand = to_df(self.db.get_brand_metrics())
            if brand.empty:
                st.warning("No brand/ESG data found.")
                return

            # Compute overall ESG
            score_cols = ["sustainability_score", "social_impact_score", "governance_score", "environmental_score"]
            for c in score_cols:
                if c not in brand.columns:
                    brand[c] = 0
            brand["overall_esg"] = brand[score_cols].mean(axis=1).round(1)

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Avg Sustainability",  f"{brand['sustainability_score'].mean():.1f}")
            k2.metric("Avg Social Impact",    f"{brand['social_impact_score'].mean():.1f}")
            k3.metric("Avg Governance",       f"{brand['governance_score'].mean():.1f}")
            k4.metric("Avg Overall ESG",      f"{brand['overall_esg'].mean():.1f}")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(brand.sort_values("overall_esg", ascending=False),
                            x="brand_name", y="overall_esg",
                            color="overall_esg", color_continuous_scale="Greens",
                            title="Overall ESG Score by Brand", text_auto=True)
                fig.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Radar chart for top brand
                top = brand.nlargest(1, "overall_esg").iloc[0]
                radar_vals = [top[c] for c in score_cols] + [top[score_cols[0]]]
                radar_labels = [c.replace("_score", "").replace("_", " ").title() for c in score_cols]
                radar_labels += [radar_labels[0]]
                fig = go.Figure(go.Scatterpolar(
                    r=radar_vals, theta=radar_labels, fill="toself",
                    line_color="#22c55e", fillcolor="rgba(34,197,94,0.15)"
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(range=[0, 100])),
                    title=f"ESG Radar — {top['brand_name']} (Top Performer)"
                )
                st.plotly_chart(fig, use_container_width=True)

            # ESG components grouped bar
            st.subheader("📊 ESG Component Breakdown")
            melted = brand.melt(id_vars=["brand_name"], value_vars=score_cols,
                                var_name="Component", value_name="Score")
            melted["Component"] = melted["Component"].str.replace("_score", "").str.replace("_", " ").str.title()
            fig = px.bar(melted, x="brand_name", y="Score", color="Component",
                        barmode="group", title="ESG Components per Brand")
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)

            # Carbon footprint
            if "carbon_footprint" in brand.columns:
                st.subheader("🌍 Carbon Footprint vs Renewable Energy")
                fig = px.scatter(brand, x="carbon_footprint", y="renewable_energy_pct",
                                size="overall_esg", color="overall_esg",
                                hover_name="brand_name", color_continuous_scale="RdYlGn",
                                title="Carbon Footprint vs Renewable Energy %",
                                labels={"carbon_footprint": "Carbon Footprint (tons CO₂)",
                                        "renewable_energy_pct": "Renewable Energy (%)"})
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Brand & ESG Data")
            st.dataframe(brand.round(2), use_container_width=True)

        # ─────────────────────────────────────────────────────────────────────────
        # 5. RISK MANAGEMENT
        # ─────────────────────────────────────────────────────────────────────────
    def render_risk_management(self):
            st.markdown('<div class="main-header">⚠️ Risk Management</div>',
                        unsafe_allow_html=True)

            risk = to_df(self.db.get_risk_data())
            if risk.empty:
                st.warning("No risk data found.")
                return

            # KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Vendors",   len(risk))
            k2.metric("High Risk",       int((risk["risk_level"] == "High").sum()))
            k3.metric("Medium Risk",     int((risk["risk_level"] == "Medium").sum()))
            k4.metric("Avg Overall Risk", f"{risk['overall_risk'].mean():.1f}%")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(risk, names="risk_level",
                            color="risk_level",
                            color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                            hole=0.4, title="Risk Level Distribution")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.scatter(risk, x="financial_risk", y="operational_risk",
                                color="risk_level", size="overall_risk",
                                hover_name="vendor_name",
                                color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                                title="Financial vs Operational Risk Matrix",
                                labels={"financial_risk": "Financial Risk (%)", "operational_risk": "Operational Risk (%)"})
                st.plotly_chart(fig, use_container_width=True)

            # Risk heatmap
            st.subheader("🗺️ Risk Heatmap by Vendor")
            risk_pivot = risk[["vendor_name", "financial_risk", "operational_risk", "compliance_risk"]].set_index("vendor_name")
            fig = go.Figure(go.Heatmap(
                z=risk_pivot.values, x=risk_pivot.columns.tolist(), y=risk_pivot.index.tolist(),
                colorscale="Reds", text=risk_pivot.values.round(1),
                texttemplate="%{text}", textfont={"size": 9},
            ))
            fig.update_layout(height=max(300, len(risk) * 22), yaxis_autorange="reversed",
                            title="Risk Scores by Component")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Risk Assessment Details")
            st.dataframe(risk.round(2), use_container_width=True)
            st.download_button("📥 Download CSV", risk.to_csv(index=False).encode(),
                            "risk_data.csv", "text/csv")

        # ─────────────────────────────────────────────────────────────────────────
        # 6. COMPLIANCE
        # ─────────────────────────────────────────────────────────────────────────
    def render_compliance(self):
            st.markdown('<div class="main-header">📋 Compliance Management</div>',
                        unsafe_allow_html=True)

            comp = to_df(self.db.get_compliance_data())
            if comp.empty:
                st.warning("No compliance data found.")
                return

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Vendors",   len(comp))
            k2.metric("Compliant",       int((comp["compliance_status"] == "Compliant").sum()))
            k3.metric("Non-Compliant",   int((comp["compliance_status"] == "Non-Compliant").sum()))
            k4.metric("Avg Audit Score", f"{comp['audit_score'].mean():.1f}")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(comp, names="compliance_status",
                            color="compliance_status",
                            color_discrete_map={"Compliant": "#22c55e",
                                                "Non-Compliant": "#ef4444",
                                                "Under Review": "#f59e0b"},
                            hole=0.4, title="Compliance Status Distribution")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(comp.sort_values("audit_score"),
                            x="audit_score", y="vendor_name", orientation="h",
                            color="compliance_status",
                            color_discrete_map={"Compliant": "#22c55e",
                                                "Non-Compliant": "#ef4444",
                                                "Under Review": "#f59e0b"},
                            title="Audit Scores by Vendor",
                            labels={"audit_score": "Audit Score", "vendor_name": ""})
                st.plotly_chart(fig, use_container_width=True)

            # Upcoming audits
            if "next_audit_date" in comp.columns:
                st.subheader("📅 Upcoming Audits (Next 90 Days)")
                comp["next_audit_date"] = pd.to_datetime(comp["next_audit_date"], errors="coerce")
                upcoming = comp[comp["next_audit_date"] <= datetime.now() + timedelta(days=90)].sort_values("next_audit_date")
                if not upcoming.empty:
                    st.dataframe(upcoming[["vendor_name", "next_audit_date", "compliance_status",
                                        "audit_score", "certifications"]].round(2),
                                use_container_width=True)
                else:
                    st.info("No audits due in the next 90 days.")

            st.subheader("📋 Full Compliance Records")
            st.dataframe(comp.round(2), use_container_width=True)
            st.download_button("📥 Download CSV", comp.to_csv(index=False).encode(),
                            "compliance_data.csv", "text/csv")

        # ─────────────────────────────────────────────────────────────────────────
        # 7. ML PREDICTIONS (NEW & REAL)
        # ─────────────────────────────────────────────────────────────────────────
    def render_ml_predictions(self):
            st.markdown('<div class="main-header">🤖 ML Predictions & Insights</div>',
                        unsafe_allow_html=True)

            if not _ML_AVAILABLE:
                st.error("scikit-learn is not installed. Run: `pip install scikit-learn`")
                return

            ml = self.ml
            if ml is None:
                st.error("ML engine could not be loaded.")
                return

            tab1, tab2, tab3, tab4 = st.tabs([
                "🎯 Risk Predictions",
                "📉 Churn Probability",
                "📈 Performance Forecast",
                "🔍 Anomaly Detection",
            ])

            # ── Tab 1: Risk Predictions ──────────────────────────────────────────
            with tab1:
                st.subheader("🎯 ML-Predicted Risk Labels")
                st.caption("Random Forest classifier trained on performance, financial, and operational features.")
                with st.spinner("Running risk model…"):
                    risk_pred = to_df(ml.predict_vendor_risks())

                if not risk_pred.empty:
                    # Agreement rate
                    if "risk_level" in risk_pred.columns and "ml_risk_label" in risk_pred.columns:
                        agree = (risk_pred["risk_level"] == risk_pred["ml_risk_label"]).mean() * 100
                        st.metric("Model-DB Agreement Rate", f"{agree:.1f}%",
                                help="% of vendors where ML prediction matches rule-based risk level")

                    col1, col2 = st.columns(2)
                    with col1:
                        ml_dist = risk_pred["ml_risk_label"].value_counts().reset_index()
                        ml_dist.columns = ["Risk Level", "Count"]
                        fig = px.pie(ml_dist, names="Risk Level", values="Count",
                                    color="Risk Level",
                                    color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                                    hole=0.4, title="ML-Predicted Risk Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        fig = px.scatter(risk_pred, x="avg_performance", y="overall_risk",
                                        color="ml_risk_label",
                                        color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                                        hover_name="name", title="Performance vs Risk Score",
                                        labels={"avg_performance": "Avg Performance (%)",
                                                "overall_risk": "Overall Risk Score (%)"})
                        st.plotly_chart(fig, use_container_width=True)

                    # Show probability columns
                    prob_cols = [c for c in risk_pred.columns if c.startswith("prob_")]
                    if prob_cols:
                        st.subheader("🎲 Risk Probability Matrix")
                        show_cols = ["name", "category", "ml_risk_label"] + prob_cols
                        show_cols = [c for c in show_cols if c in risk_pred.columns]
                        st.dataframe(risk_pred[show_cols].round(3), use_container_width=True)

                else:
                    st.info("No risk predictions available.")

                col_retrain, _ = st.columns([1, 4])
                if col_retrain.button("🔁 Retrain Models"):
                    with st.spinner("Retraining…"):
                        ml.retrain()
                    st.success("✅ Models retrained successfully!")

            # ── Tab 2: Churn Probability ─────────────────────────────────────────
            with tab2:
                st.subheader("📉 Vendor Churn Probability")
                st.caption("Gradient Boosting Regressor predicts likelihood of vendor churn (0 = low, 1 = high).")
                with st.spinner("Running churn model…"):
                    churn = to_df(ml.predict_churn())

                if not churn.empty:
                    k1, k2, k3 = st.columns(3)
                    k1.metric("High Churn Risk",   int((churn["churn_risk"] == "High").sum()))
                    k2.metric("Medium Churn Risk",  int((churn["churn_risk"] == "Medium").sum()))
                    k3.metric("Avg Churn Prob",     f"{churn['churn_probability'].mean():.2f}")

                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.bar(churn.sort_values("churn_probability", ascending=False).head(15),
                                    x="churn_probability", y="name", orientation="h",
                                    color="churn_risk",
                                    color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                                    title="Top 15 Vendors by Churn Probability",
                                    labels={"churn_probability": "Churn Probability", "name": ""})
                        fig.update_layout(yaxis={"categoryorder": "total ascending"})
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        fig = px.histogram(churn, x="churn_probability", nbins=15,
                                        color="churn_risk",
                                        color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"},
                                        title="Churn Probability Distribution",
                                        labels={"churn_probability": "Churn Probability"})
                        st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(churn.round(3), use_container_width=True)
                else:
                    st.info("No churn predictions available.")

            # ── Tab 3: Performance Forecast ──────────────────────────────────────
            with tab3:
                st.subheader("📈 6-Month Performance Forecast")
                st.caption("Linear Regression trend extrapolation per vendor using historical performance data.")
                with st.spinner("Generating forecasts…"):
                    forecast = to_df(ml.forecast_performance(months_ahead=6))

                if not forecast.empty:
                    # Vendor selector
                    vendors_fcast = forecast["vendor_name"].unique().tolist()
                    sel_vendors = st.multiselect("Select Vendors to Compare",
                                                vendors_fcast, default=vendors_fcast[:5])
                    fcast_filt = forecast[forecast["vendor_name"].isin(sel_vendors)] if sel_vendors else forecast

                    forecast["forecast_date"] = pd.to_datetime(forecast["forecast_date"])
                    fig = px.line(fcast_filt, x="forecast_date", y="predicted_score",
                                color="vendor_name", markers=True,
                                title="6-Month Performance Forecast by Vendor",
                                labels={"predicted_score": "Predicted Score (%)",
                                        "forecast_date": "Date"})
                    fig.add_hline(y=70, line_dash="dot", line_color="red",
                                annotation_text="Performance Threshold (70%)")
                    st.plotly_chart(fig, use_container_width=True)

                    # Summary table
                    fcast_summary = forecast.groupby("vendor_name").agg(
                        min_forecast=("predicted_score", "min"),
                        max_forecast=("predicted_score", "max"),
                        avg_forecast=("predicted_score", "mean"),
                    ).reset_index().round(2)
                    st.dataframe(fcast_summary, use_container_width=True)
                else:
                    st.info("Not enough historical data for forecasts. Need at least 3 months of data per vendor.")

            # ── Tab 4: Anomaly Detection ──────────────────────────────────────────
            with tab4:
                st.subheader("🔍 Anomaly Detection")
                st.caption("Isolation Forest detects vendors whose metrics deviate significantly from the norm.")
                with st.spinner("Running anomaly detection…"):
                    anomalies = to_df(ml.detect_anomalies())

                if not anomalies.empty:
                    num_anomalies = int(anomalies["is_anomaly"].sum())
                    k1, k2 = st.columns(2)
                    k1.metric("Anomalous Vendors Detected", num_anomalies)
                    k2.metric("Anomaly Rate", f"{num_anomalies/len(anomalies)*100:.1f}%")

                    col1, col2 = st.columns(2)
                    with col1:
                        fig = px.scatter(anomalies, x="avg_performance", y="anomaly_score",
                                        color="is_anomaly",
                                        color_discrete_map={True: "#ef4444", False: "#22c55e"},
                                        hover_name="name",
                                        title="Anomaly Score vs Performance",
                                        labels={"avg_performance": "Avg Performance (%)",
                                                "anomaly_score": "Anomaly Score (lower = more anomalous)"})
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        anom_only = anomalies[anomalies["is_anomaly"]]
                        if not anom_only.empty:
                            fig = px.bar(anom_only, x="name", y="anomaly_score",
                                        color="category", title="Anomalous Vendors",
                                        labels={"anomaly_score": "Anomaly Score", "name": ""})
                            fig.update_layout(xaxis_tickangle=-35)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.success("✅ No anomalies detected!")

                    st.subheader("📋 Anomaly Detection Results")
                    st.dataframe(anomalies.round(3), use_container_width=True)
                else:
                    st.info("No anomaly data available.")

        # ─────────────────────────────────────────────────────────────────────────
        # 8. REPORTS
        # ─────────────────────────────────────────────────────────────────────────
    def render_reports(self):
            st.markdown('<div class="main-header">📄 Reports & Export</div>',
                        unsafe_allow_html=True)

            if not _REPORT_AVAILABLE or self.report_gen is None:
                st.error("Report generator not available. Install: `pip install reportlab xlsxwriter`")
                return

            col1, col2, col3 = st.columns(3)
            report_type = col1.selectbox("Report Type", [
                "Vendor Performance", "Financial Summary", "Risk Assessment",
                "Compliance Status", "Executive Summary"])
            fmt = col2.selectbox("Format", ["PDF", "Excel", "HTML"])
            col3.markdown("<br>", unsafe_allow_html=True)
            if col3.button("📊 Generate Report", type="primary", use_container_width=True):
                with st.spinner("Generating…"):
                    result = self.report_gen.generate_report(report_type, fmt)
                if "✅" in result or "generated" in result.lower():
                    fpath = result.split(":")[-1].strip()
                    st.success(f"✅ Report generated: `{fpath}`")
                    try:
                        with open(fpath, "rb") as f:
                            data = f.read()
                        mime_map = {"PDF": "application/pdf",
                                    "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    "HTML": "text/html"}
                        st.download_button(f"⬇️ Download {fmt}",
                                        data, os.path.basename(fpath), mime_map.get(fmt, "application/octet-stream"))
                        if fmt == "HTML":
                            with open(fpath, "r", encoding="utf-8") as f:
                                st.components.v1.html(f.read(), height=600, scrolling=True)
                    except Exception as e:
                        st.error(f"Could not read file: {e}")
                else:
                    st.error(result)

            st.divider()
            st.subheader("📂 Previously Generated Reports")
            reports = self.report_gen.get_generated_reports()
            if reports:
                df_rep = pd.DataFrame(reports)
                df_rep["size"] = df_rep["size"].apply(lambda x: f"{x/1024:.1f} KB")
                st.dataframe(df_rep[["name", "size", "created"]], use_container_width=True)
            else:
                st.info("No reports generated yet.")

        # ─────────────────────────────────────────────────────────────────────────
        # 9. VENDOR PORTAL
        # ─────────────────────────────────────────────────────────────────────────
    def render_vendor_portal(self):
            st.markdown('<div class="main-header">🏢 Vendor Portal</div>',
                        unsafe_allow_html=True)

            vendors = to_df(self.db.get_vendors())
            tab1, tab2, tab3 = st.tabs(["➕ Add Vendor", "📊 Performance View", "📝 Documents"])

            with tab1:
                st.subheader("Add New Vendor")
                with st.form("add_vendor_form"):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Company Name *")
                    category = c2.selectbox("Category", ["IT Services", "Logistics", "Manufacturing",
                                                        "Consulting", "Raw Materials", "Marketing", "Facilities"])
                    email = c1.text_input("Email")
                    phone = c2.text_input("Phone")
                    contract_val = c1.number_input("Contract Value ($)", 0, 10_000_000, 50000, 1000)
                    risk_level = c2.selectbox("Initial Risk Level", ["Low", "Medium", "High"])
                    status = c1.selectbox("Status", ["Active", "Inactive", "Under Review"])
                    country = c2.selectbox("Country", ["USA", "UK", "Germany", "India", "Canada", "Australia", "Japan"])
                    submitted = st.form_submit_button("➕ Add Vendor", type="primary")
                    if submitted:
                        if not name:
                            st.error("Company name is required.")
                        else:
                            self.db.add_vendor(name, email, phone, category, status,
                                            risk_level, contract_val, 0, country)
                            st.success(f"✅ Vendor **{name}** added successfully!")
                            st.rerun()

            with tab2:
                st.subheader("Vendor Performance Summary")
                vp = to_df(self.db.get_vendors_with_performance())
                if not vp.empty:
                    sel_vendor = st.selectbox("Select Vendor", vp["name"].unique())
                    v_row = vp[vp["name"] == sel_vendor].iloc[0]
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Avg Performance",  f"{v_row.get('avg_performance', 0):.1f}%")
                    m2.metric("Avg On-Time",       f"{v_row.get('avg_on_time', 0):.1f}%")
                    m3.metric("Avg Quality",       f"{v_row.get('avg_quality', 0):.1f}%")
                    m4.metric("Contract Value",    fmt_currency(v_row.get("contract_value", 0)))

                    # Performance history
                    perf = to_df(self.db.get_performance_data())
                    if not perf.empty and "vendor_name" in perf.columns:
                        v_perf = perf[perf["vendor_name"] == sel_vendor].sort_values("metric_date")
                        if not v_perf.empty:
                            fig = px.line(v_perf, x="metric_date", y="overall_score",
                                        markers=True, title=f"{sel_vendor} — Historical Performance",
                                        labels={"overall_score": "Score (%)", "metric_date": "Date"})
                            fig.update_layout(yaxis=dict(range=[0, 100]))
                            st.plotly_chart(fig, use_container_width=True)

            with tab3:
                st.subheader("Document Management")
                docs = pd.DataFrame({
                    "Document": ["Certificate of Insurance", "W-9 / Tax Form",
                                "Quality Certifications", "Compliance Documents", "NDA"],
                    "Status": ["✅ Approved", "✅ Approved", "🔄 Under Review", "✅ Approved", "✅ Approved"],
                    "Last Updated": ["2025-01-15", "2025-01-20", "2025-02-01", "2025-02-28", "2024-12-01"],
                })
                st.dataframe(docs, use_container_width=True)
                st.file_uploader("Upload New Document", type=["pdf", "doc", "docx", "xlsx"])

        # ─────────────────────────────────────────────────────────────────────────
        # 10. SETTINGS
        # ─────────────────────────────────────────────────────────────────────────
    def render_settings(self):
            st.markdown('<div class="main-header">⚙️ Settings</div>',
                        unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs(["👤 User Preferences", "🔧 System Config", "📊 Data Management"])

            with tab1:
                st.subheader("User Preferences")
                c1, c2 = st.columns(2)
                c1.selectbox("Dashboard Theme", ["Light", "Dark", "Auto"])
                c2.selectbox("Language", ["English", "Spanish", "French", "German"])
                c1.slider("Auto-Refresh Interval (min)", 1, 60, 5)
                c2.multiselect("Default Views", ["Overview", "Performance", "Financial", "Risk", "Compliance"])
                c1.checkbox("Email Notifications", value=True)
                c2.checkbox("Desktop Notifications", value=False)
                if st.button("💾 Save Preferences"):
                    st.success("Preferences saved!")

            with tab2:
                st.subheader("System Configuration")
                st.number_input("Performance Alert Threshold (%)", 0, 100,
                                st.session_state.perf_threshold)
                st.number_input("High Risk Score Threshold (%)", 0, 100, 65)
                st.number_input("Churn Probability Threshold", 0.0, 1.0, 0.5, 0.05)
                st.number_input("Report Auto-Archive (days)", 30, 365, 90)
                if st.button("💾 Update Config"):
                    st.success("System config updated!")

            with tab3:
                st.subheader("Data Management")
                c1, c2, c3 = st.columns(3)
                if c1.button("🔄 Re-seed Database", use_container_width=True):
                    with st.spinner("Seeding…"):
                        self.db._seed_all()
                    st.success("Database re-seeded!")
                if c2.button("🤖 Retrain ML Models", use_container_width=True):
                    if self.ml:
                        with st.spinner("Retraining…"):
                            self.ml.retrain()
                        st.success("Models retrained!")
                    else:
                        st.warning("ML engine not available.")
                if c3.button("🧹 Clear Reports Folder", use_container_width=True):
                    import glob
                    for f in glob.glob("reports/*"):
                        try:
                            os.remove(f)
                        except Exception:
                            pass
                    st.success("Reports cleared!")

                st.warning("⚠️ Re-seeding replaces all demo data. This cannot be undone.")

        # ─────────────────────────────────────────────────────────────────────────
        # MAIN RUN
        # ─────────────────────────────────────────────────────────────────────────
    def run(self):
            inject_styles()
            self.render_sidebar()

            if st.session_state.user is None:
                st.info("👈 Please log in using the sidebar to access the dashboard.")
                st.markdown("""
                ### 🤖 ML-Driven Vendor Optimization Platform
                A full-stack vendor analytics platform with **real machine learning models**:
                - 🎯 **Risk Scoring** — Random Forest classifier
                - 📉 **Churn Prediction** — Gradient Boosting regressor
                - 📈 **Performance Forecasting** — Linear trend extrapolation
                - 🔍 **Anomaly Detection** — Isolation Forest
                
                **Demo credentials:** `admin` / `admin123`
                """)
                return

            nav_map = {
                "🏠 Overview":          self.render_overview,
                "📊 Vendor Performance": self.render_vendor_performance,
                "💰 Financial Analytics": self.render_financial_analytics,
                "🌱 Brand & ESG":        self.render_brand_esg,
                "⚠️ Risk Management":    self.render_risk_management,
                "📋 Compliance":         self.render_compliance,
                "🤖 ML Predictions":     self.render_ml_predictions,
                "📄 Reports":            self.render_reports,
                "🏢 Vendor Portal":      self.render_vendor_portal,
                "⚙️ Settings":           self.render_settings,
            }
            page = st.session_state.get("selected_nav", "🏠 Overview")
            nav_map.get(page, self.render_overview)()


    # ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dashboard = VendorDashboard()
    dashboard.run()

    