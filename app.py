import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from core_modules.auth import Authentication
from core_modules.database import DatabaseManager
from core_modules.analytics import AnalyticsEngine
from core_modules.email_service import EmailService
from core_modules.config import Config
from core_modules.api import APIManager
from enhancements.financial_analytics import FinancialAnalytics
from enhancements.predictive_analytics import PredictiveAnalytics
from enhancements.compliance_manager import ComplianceManager
from enhancements.workflow_engine import WorkflowEngine
from enhancements.report_generator import ReportGenerator
from enhancements.benchmarking import Benchmarking
from enhancements.vendor_collaboration import VendorCollaboration


class VendorDashboard:
    def __init__(self):
        self.config = Config()
        self.auth = Authentication()
        self.db = DatabaseManager()
        self.analytics = AnalyticsEngine(self.db)
        self.email_service = EmailService()
        self.api_manager = APIManager()
        self.financial_analytics = FinancialAnalytics(self.db)
        self.predictive_analytics = PredictiveAnalytics(self.db)
        self.compliance_manager = ComplianceManager(self.db)
        self.workflow_engine = WorkflowEngine(self.db)
        self.report_generator = ReportGenerator(self.db)
        self.benchmarking = Benchmarking(self.db)
        self.vendor_collaboration = VendorCollaboration(self.db)

        self.setup_page_config()
        self.initialize_session_state()

    # -------------------------------------------------
    # SESSION CONFIG
    # -------------------------------------------------
    def initialize_session_state(self):
        if 'selected_vendor' not in st.session_state:
            st.session_state.selected_vendor = None
        if 'performance_threshold' not in st.session_state:
            st.session_state.performance_threshold = 70
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False

    def setup_page_config(self):
        st.set_page_config(page_title="Vendor Performance Dashboard", page_icon="📊", layout="wide")
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.3rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1.5rem;
            font-weight: 600;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1.2rem;
            border-radius: 8px;
            border-left: 4px solid #1f77b4;
            border: 1px solid #e9ecef;
        }
        </style>
        """, unsafe_allow_html=True)

    # -------------------------------------------------
    # SIDEBAR
    # -------------------------------------------------
    def render_sidebar(self):
        with st.sidebar:
            st.title("Vendor Dashboard")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.rerun()
            with col2:
                if st.button("🏠 Overview", use_container_width=True):
                    st.session_state.selected_nav = "Overview Dashboard"
                    st.rerun()

            if 'user' not in st.session_state:
                st.session_state.user = None

            if st.session_state.user is None:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("Login"):
                        user = self.auth.authenticate(username, password)
                        if user:
                            st.session_state.user = user
                            st.success(f"Welcome {user['name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
            else:
                st.success(f"👋 {st.session_state.user['name']}")
                if st.button("Logout"):
                    st.session_state.user = None
                    st.rerun()

            if st.session_state.user:
                st.divider()
                st.subheader("Navigation")
                nav_options = [
                    "Overview Dashboard",
                    "Vendor Performance",
                    "Financial Analytics",
                    "Brand & ESG Analytics",
                    "Risk Management",
                    "Compliance",
                    "Reports",
                    "Vendor Portal",
                    "Settings"
                ]
                st.session_state.selected_nav = st.selectbox("Go to", nav_options, key="nav_select")

                st.divider()
                st.subheader("Filters")
                st.session_state.filters = {
                    'time_period': st.selectbox("Time Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All Time"]),
                    'performance_threshold': st.slider("Performance Alert Threshold", 0, 100, 70),
                }

        # -------------------------------------------------
    # OVERVIEW DASHBOARD
    # -------------------------------------------------
    def render_overview_dashboard(self):
        st.markdown('<div class="main-header">📈 Vendor Performance Overview</div>', unsafe_allow_html=True)

        # Get vendor data directly
        vendors = self.db.get_vendors()
        total_vendors = len(vendors) if not vendors.empty else 0
        
        # Calculate metrics based on your actual columns
        if not vendors.empty:
            # Calculate average contract value as performance proxy
            if 'contract_value' in vendors.columns:
                avg_contract_value = vendors['contract_value'].mean()
                # Convert to performance score (0-100 scale)
                max_contract = vendors['contract_value'].max()
                avg_perf = (avg_contract_value / max_contract * 100) if max_contract > 0 else 75.0
            else:
                avg_perf = 75.0
            
            # Calculate risk count based on your risk_level column
            if 'risk_level' in vendors.columns:
                risk_count = (vendors['risk_level'].str.lower() == 'high').sum()
            else:
                risk_count = 0
            
            # Calculate active vendors based on status
            if 'status' in vendors.columns:
                active_vendors = (vendors['status'].str.lower() == 'active').sum()
            else:
                active_vendors = total_vendors
            
            # Calculate total contract value
            if 'contract_value' in vendors.columns:
                total_contract_value = vendors['contract_value'].sum()
            else:
                total_contract_value = 0
        else:
            avg_perf = 75.0
            risk_count = 0
            active_vendors = 0
            total_contract_value = 0

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Vendors", total_vendors)
        col2.metric("Active Vendors", active_vendors)
        col3.metric("High Risk Vendors", risk_count)
        col4.metric("Total Contract Value", f"${total_contract_value:,.0f}")

        st.divider()
        st.subheader("Performance Insights")

        if not vendors.empty:
            # Use contract value as performance indicator
            if 'contract_value' in vendors.columns and 'name' in vendors.columns:
                # Show top vendors by contract value
                top_vendors = vendors.nlargest(15, 'contract_value')
                fig_bar = px.bar(top_vendors, x='name', y='contract_value',
                                 color='contract_value', color_continuous_scale="Blues",
                                 title="Top 15 Vendors by Contract Value",
                                 labels={'contract_value': 'Contract Value ($)', 'name': 'Vendor Name'})
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)
                
                # Vendor distribution by category
                if 'category' in vendors.columns:
                    st.subheader("Vendor Distribution by Category")
                    category_counts = vendors['category'].value_counts().reset_index()
                    category_counts.columns = ['category', 'count']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        fig_pie = px.pie(category_counts, names='category', values='count',
                                       title="Vendor Distribution by Category")
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Average contract value by category
                        category_contracts = vendors.groupby('category')['contract_value'].mean().reset_index()
                        fig_bar_cat = px.bar(category_contracts, x='category', y='contract_value',
                                           title="Average Contract Value by Category",
                                           color='contract_value', color_continuous_scale="Viridis",
                                           labels={'contract_value': 'Avg Contract Value ($)', 'category': 'Category'})
                        st.plotly_chart(fig_bar_cat, use_container_width=True)
                
                # Risk distribution
                if 'risk_level' in vendors.columns:
                    st.subheader("Risk Level Distribution")
                    risk_counts = vendors['risk_level'].value_counts().reset_index()
                    risk_counts.columns = ['risk_level', 'count']
                    
                    fig_risk = px.pie(risk_counts, names='risk_level', values='count',
                                    title="Vendor Risk Level Distribution",
                                    color='risk_level',
                                    color_discrete_map={'Low': 'green', 'Medium': 'orange', 'High': 'red'})
                    st.plotly_chart(fig_risk, use_container_width=True)
                
                # Contract status overview
                if 'status' in vendors.columns:
                    st.subheader("Contract Status Overview")
                    status_counts = vendors['status'].value_counts().reset_index()
                    status_counts.columns = ['status', 'count']
                    
                    fig_status = px.bar(status_counts, x='status', y='count',
                                      title="Vendor Contract Status",
                                      color='status', text_auto=True)
                    st.plotly_chart(fig_status, use_container_width=True)
            
            else:
                st.warning(f"Available columns: {list(vendors.columns)}")
                
                # Show basic data table if we can't create charts
                st.subheader("Vendor Data Overview")
                st.dataframe(vendors.head(10), use_container_width=True)
        else:
            st.info("No vendor data available.")
      # -------------------------------------------------
    # VENDOR PERFORMANCE
    # -------------------------------------------------
    def render_vendor_performance(self):
        st.markdown('<div class="main-header">📊 Vendor Performance Analysis</div>', unsafe_allow_html=True)
        
        # Get vendor data
        vendors_data = self.db.get_vendors_with_performance()
        
        # If empty, try alternative method
        if vendors_data.empty:
            vendors_data = self.db.get_vendors()
        
        st.success(f"📊 Loaded {len(vendors_data)} vendor records")
        
        if not vendors_data.empty:
            # Show data structure info
            with st.expander("🔍 View Data Structure"):
                st.write("Available columns:", list(vendors_data.columns))
                st.dataframe(vendors_data.head(), use_container_width=True)
            
            # Vendor Comparison Section - Using contract value as performance metric
            st.subheader("🔍 Compare Vendors")
            
            # Use contract value as the main metric since we don't have performance_score
            vendor_name_col = 'name' if 'name' in vendors_data.columns else vendors_data.columns[0]
            performance_col = 'contract_value' if 'contract_value' in vendors_data.columns else None
            
            if vendor_name_col and performance_col:
                col1, col2 = st.columns(2)
                with col1:
                    vendor_options = vendors_data[vendor_name_col].unique()
                    v1 = st.selectbox("Select Vendor 1", vendor_options)
                with col2:
                    v2 = st.selectbox("Select Vendor 2", [v for v in vendor_options if v != v1])

                if v1 and v2:
                    # Get vendor data
                    v1_data = vendors_data[vendors_data[vendor_name_col] == v1]
                    v2_data = vendors_data[vendors_data[vendor_name_col] == v2]
                    
                    if not v1_data.empty and not v2_data.empty:
                        v1_value = float(v1_data[performance_col].iloc[0])
                        v2_value = float(v2_data[performance_col].iloc[0])
                        diff = v1_value - v2_value
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric(v1, f"${v1_value:,.0f}")
                        col2.metric(v2, f"${v2_value:,.0f}")
                        col3.metric("Difference", f"${diff:,.0f}")

                        # Comparison chart
                        st.divider()
                        comparison_data = vendors_data[vendors_data[vendor_name_col].isin([v1, v2])]
                        fig_comp = px.bar(comparison_data, x=vendor_name_col, y=performance_col, 
                                        color=vendor_name_col, 
                                        title="Vendor Contract Value Comparison", 
                                        labels={performance_col: 'Contract Value ($)', vendor_name_col: 'Vendor'},
                                        text_auto=True)
                        st.plotly_chart(fig_comp, use_container_width=True)
            
            # Contract Value Distribution
            st.subheader("📈 Contract Value Distribution")
            
            if performance_col:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Histogram of contract values
                    fig_hist = px.histogram(vendors_data, x=performance_col, 
                                          title="Contract Value Distribution",
                                          nbins=10, color_discrete_sequence=['#1f77b4'],
                                          labels={performance_col: 'Contract Value ($)'})
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # Top 10 vendors by contract value
                    top_vendors = vendors_data.nlargest(10, performance_col)
                    fig_bar = px.bar(top_vendors, x=vendor_name_col, y=performance_col,
                                   title="Top 10 Vendors by Contract Value",
                                   color=performance_col,
                                   color_continuous_scale="Viridis",
                                   labels={performance_col: 'Contract Value ($)', vendor_name_col: 'Vendor'})
                    fig_bar.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_bar, use_container_width=True)

            # Analysis by Category
            category_col = 'category' if 'category' in vendors_data.columns else None
            if category_col and performance_col:
                st.subheader("🏷️ Analysis by Category")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Average contract value by category
                    category_avg = vendors_data.groupby(category_col)[performance_col].mean().reset_index()
                    fig_cat_avg = px.bar(category_avg, x=category_col, y=performance_col,
                                       title="Average Contract Value by Category",
                                       text_auto=True,
                                       labels={performance_col: 'Avg Contract Value ($)', category_col: 'Category'})
                    st.plotly_chart(fig_cat_avg, use_container_width=True)
                
                with col2:
                    # Vendor count by category
                    category_count = vendors_data[category_col].value_counts().reset_index()
                    category_count.columns = [category_col, 'count']
                    fig_cat_count = px.pie(category_count, names=category_col, values='count',
                                         title="Vendor Count by Category")
                    st.plotly_chart(fig_cat_count, use_container_width=True)

            # Risk Analysis
            if 'risk_level' in vendors_data.columns:
                st.subheader("⚠️ Risk Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Risk level distribution
                    risk_counts = vendors_data['risk_level'].value_counts().reset_index()
                    risk_counts.columns = ['risk_level', 'count']
                    fig_risk = px.pie(risk_counts, names='risk_level', values='count',
                                    title="Risk Level Distribution",
                                    color='risk_level',
                                    color_discrete_map={'Low': 'green', 'Medium': 'orange', 'High': 'red'})
                    st.plotly_chart(fig_risk, use_container_width=True)
                
                with col2:
                    # Average contract value by risk level
                    if performance_col:
                        risk_contracts = vendors_data.groupby('risk_level')[performance_col].mean().reset_index()
                        fig_risk_contracts = px.bar(risk_contracts, x='risk_level', y=performance_col,
                                                  title="Avg Contract Value by Risk Level",
                                                  color='risk_level',
                                                  color_discrete_map={'Low': 'green', 'Medium': 'orange', 'High': 'red'},
                                                  labels={performance_col: 'Avg Contract Value ($)', 'risk_level': 'Risk Level'})
                        st.plotly_chart(fig_risk_contracts, use_container_width=True)

            # Vendor Performance Table with Filters
            st.subheader("📋 Vendor Details")
            
            # Add filters
            col1, col2, col3 = st.columns(3)
            filtered_data = vendors_data.copy()
            
            with col1:
                if vendor_name_col:
                    selected_vendors = st.multiselect("Filter by Vendor", vendors_data[vendor_name_col].unique())
                    if selected_vendors:
                        filtered_data = filtered_data[filtered_data[vendor_name_col].isin(selected_vendors)]
            
            with col2:
                if category_col:
                    selected_categories = st.multiselect("Filter by Category", vendors_data[category_col].unique())
                    if selected_categories:
                        filtered_data = filtered_data[filtered_data[category_col].isin(selected_categories)]
            
            with col3:
                if 'risk_level' in vendors_data.columns:
                    selected_risks = st.multiselect("Filter by Risk Level", vendors_data['risk_level'].unique())
                    if selected_risks:
                        filtered_data = filtered_data[filtered_data['risk_level'].isin(selected_risks)]
            
            # Contract value filter
            if performance_col:
                min_val = int(vendors_data[performance_col].min())
                max_val = int(vendors_data[performance_col].max())
                value_range = st.slider("Contract Value Range", 
                                      min_value=min_val, 
                                      max_value=max_val,
                                      value=(min_val, max_val))
                filtered_data = filtered_data[(filtered_data[performance_col] >= value_range[0]) & 
                                           (filtered_data[performance_col] <= value_range[1])]
            
            st.dataframe(filtered_data, use_container_width=True)
            
            # Export option
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name="vendor_analysis.csv",
                mime="text/csv"
            )

    # -------------------------------------------------
    # FINANCIAL ANALYTICS
    # -------------------------------------------------
    def render_financial_analytics(self):
        st.markdown('<div class="main-header">💰 Financial Analytics</div>', unsafe_allow_html=True)
        
        # Create comprehensive financial data
        financial_data = pd.DataFrame({
            'category': ['IT Services', 'Logistics', 'Manufacturing', 'Consulting', 'Raw Materials', 'Marketing', 'Facilities'],
            'cost_savings': [45000, 32000, 28000, 35000, 22000, 18000, 15000],
            'total_spend': [250000, 180000, 320000, 120000, 280000, 90000, 110000],
            'vendor_count': [12, 8, 15, 6, 9, 7, 5],
            'savings_rate': [18.0, 17.8, 8.8, 29.2, 7.9, 20.0, 13.6],
            'qtr': ['Q1', 'Q1', 'Q1', 'Q1', 'Q1', 'Q1', 'Q1']
        })
        
        st.success(f"💰 Financial data loaded with {len(financial_data)} categories")
        
        # Financial Metrics
        total_savings = financial_data['cost_savings'].sum()
        total_spend = financial_data['total_spend'].sum()
        overall_savings_rate = (total_savings / total_spend * 100)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Savings", f"${total_savings:,.0f}")
        col2.metric("Total Spend", f"${total_spend:,.0f}")
        col3.metric("Savings Rate", f"{overall_savings_rate:.1f}%")
        col4.metric("Categories", len(financial_data))
        
        st.divider()
        
        # Savings Analysis
        st.subheader("💵 Savings Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar = px.bar(financial_data, x="category", y="cost_savings",
                           title="Cost Savings by Category",
                           color="cost_savings", color_continuous_scale="Viridis",
                           text_auto=True)
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            fig_pie = px.pie(financial_data, names="category", values="cost_savings",
                           title="Savings Distribution by Category",
                           hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Savings Rate Analysis
        st.subheader("📊 Savings Rate Performance")
        fig_rate = px.bar(financial_data, x="category", y="savings_rate",
                         title="Savings Rate by Category (%)",
                         color="savings_rate", color_continuous_scale="RdYlGn",
                         text_auto=True)
        st.plotly_chart(fig_rate, use_container_width=True)
        
        # Financial Data Table
        st.subheader("📋 Financial Data Details")
        st.dataframe(financial_data, use_container_width=True)

    # -------------------------------------------------
    # BRAND & ESG ANALYTICS
    # -------------------------------------------------
    def render_brand_esg_analytics(self):
        st.markdown('<div class="main-header">🌱 Brand & ESG Analytics</div>', unsafe_allow_html=True)
        
        # Create comprehensive brand and ESG data
        brand_data = pd.DataFrame({
            'brand_name': ['EcoTech Solutions', 'Green Logistics Inc', 'Sustainable Manufacturing Co', 
                          'Ethical Consulting Group', 'Clean Energy Partners', 'Social Impact Corp',
                          'Environmental Services Ltd', 'Carbon Neutral Industries'],
            'sustainability_score': [88, 92, 85, 79, 95, 82, 76, 89],
            'social_impact_score': [85, 78, 82, 91, 87, 94, 79, 83],
            'governance_score': [90, 85, 88, 92, 84, 89, 81, 86],
            'environmental_score': [92, 89, 83, 75, 96, 80, 78, 91],
            'overall_esg_score': [88.8, 86.0, 84.5, 84.3, 90.5, 86.3, 78.5, 87.3],
            'carbon_footprint': [120, 180, 320, 95, 65, 110, 280, 150],
            'renewable_energy_pct': [85, 65, 45, 90, 95, 75, 35, 70]
        })

        st.success(f"🌱 ESG data loaded for {len(brand_data)} brands")
        
        # ESG Metrics Overview
        st.subheader("📊 ESG Performance Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Sustainability", f"{brand_data['sustainability_score'].mean():.1f}")
        col2.metric("Avg Social Impact", f"{brand_data['social_impact_score'].mean():.1f}")
        col3.metric("Avg Governance", f"{brand_data['governance_score'].mean():.1f}")
        col4.metric("Avg Overall ESG", f"{brand_data['overall_esg_score'].mean():.1f}")
        
        st.divider()
        
        # ESG Scores Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar = px.bar(brand_data, x="brand_name", y="overall_esg_score",
                           color="overall_esg_score", color_continuous_scale="Greens",
                           title="Overall ESG Scores by Brand", text_auto=True)
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Radar chart for top brand
            top_brand = brand_data.nlargest(1, 'overall_esg_score').iloc[0]
            radar_categories = ['sustainability_score', 'social_impact_score', 'governance_score', 'environmental_score']
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[top_brand[col] for col in radar_categories],
                theta=[col.replace('_score', '').title() for col in radar_categories],
                fill='toself',
                name=top_brand['brand_name']
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title=f"ESG Radar - {top_brand['brand_name']} (Top Performer)"
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        
        # ESG Components Comparison
        st.subheader("📈 ESG Components Comparison")
        esg_components = brand_data.melt(id_vars=['brand_name'], 
                                       value_vars=['sustainability_score', 'social_impact_score', 'governance_score'],
                                       var_name='ESG Component', value_name='Score')
        
        fig_components = px.bar(esg_components, x="brand_name", y="Score", color="ESG Component",
                              title="ESG Components Comparison", barmode="group")
        fig_components.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_components, use_container_width=True)
        
        # Brand Data Table
        st.subheader("📋 Brand & ESG Data Details")
        st.dataframe(brand_data, use_container_width=True)

    # -------------------------------------------------
    # RISK MANAGEMENT
    # -------------------------------------------------
    def render_risk_management(self):
        st.markdown('<div class="main-header">⚠️ Risk Management</div>', unsafe_allow_html=True)
        
        st.info("🚧 Risk Management module is under development")
        
        # Sample risk data
        risk_data = pd.DataFrame({
            'vendor_name': [f'Vendor {i}' for i in range(1, 16)],
            'risk_level': np.random.choice(['Low', 'Medium', 'High', 'Critical'], 15, p=[0.5, 0.3, 0.15, 0.05]),
            'risk_score': np.random.randint(20, 95, 15),
            'last_assessment': pd.date_range('2024-01-01', periods=15, freq='D'),
            'mitigation_status': np.random.choice(['Not Started', 'In Progress', 'Completed', 'Monitoring'], 15),
            'financial_risk': np.random.randint(1, 10, 15),
            'operational_risk': np.random.randint(1, 10, 15),
            'compliance_risk': np.random.randint(1, 10, 15)
        })
        
        st.subheader("Risk Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Vendors", len(risk_data))
        col2.metric("High Risk", (risk_data['risk_level'] == 'High').sum())
        col3.metric("Critical Risk", (risk_data['risk_level'] == 'Critical').sum())
        col4.metric("Avg Risk Score", f"{risk_data['risk_score'].mean():.1f}")
        
        # Risk Distribution
        st.subheader("Risk Distribution")
        fig_risk = px.pie(risk_data, names='risk_level', title='Vendor Risk Level Distribution')
        st.plotly_chart(fig_risk, use_container_width=True)
        
        # Risk Data Table
        st.subheader("Risk Assessment Details")
        st.dataframe(risk_data, use_container_width=True)

    # -------------------------------------------------
    # COMPLIANCE
    # -------------------------------------------------
    def render_compliance(self):
        st.markdown('<div class="main-header">📋 Compliance Management</div>', unsafe_allow_html=True)
        
        st.info("🚧 Compliance module is under development")
        
        # Sample compliance data
        compliance_data = pd.DataFrame({
            'vendor_name': [f'Vendor {i}' for i in range(1, 12)],
            'compliance_status': np.random.choice(['Compliant', 'Non-Compliant', 'Under Review'], 11),
            'last_audit': pd.date_range('2024-01-01', periods=11, freq='M'),
            'audit_score': np.random.randint(60, 100, 11),
            'certifications': ['ISO 9001, ISO 14001', 'ISO 9001', 'SOC 2', 'ISO 27001', 'HIPAA', 
                              'ISO 9001, ISO 14001', 'SOC 2, ISO 27001', 'ISO 9001', 'HIPAA, SOC 2', 
                              'ISO 14001', 'ISO 9001, SOC 2'],
            'next_audit_due': pd.date_range('2024-07-01', periods=11, freq='M')
        })
        
        st.subheader("Compliance Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Vendors", len(compliance_data))
        col2.metric("Compliant", (compliance_data['compliance_status'] == 'Compliant').sum())
        col3.metric("Non-Compliant", (compliance_data['compliance_status'] == 'Non-Compliant').sum())
        col4.metric("Avg Audit Score", f"{compliance_data['audit_score'].mean():.1f}")
        
        # Compliance Status
        st.subheader("Compliance Status")
        fig_compliance = px.bar(compliance_data, x='vendor_name', y='audit_score', 
                              color='compliance_status', title='Vendor Compliance Status')
        st.plotly_chart(fig_compliance, use_container_width=True)
        
        # Compliance Data Table
        st.subheader("Compliance Details")
        st.dataframe(compliance_data, use_container_width=True)
    # -------------------------------------------------
    # REPORTS
    # -------------------------------------------------
    def render_reports(self):
        st.markdown('<div class="main-header">📄 Reports & Analytics</div>', unsafe_allow_html=True)

        st.subheader("Generate Reports")

        col1, col2 = st.columns(2)

        with col1:
            report_type = st.selectbox(
                "Select Report Type",
                [
                    "Vendor Performance",
                    "Financial Summary",
                    "Risk Assessment",
                    "Compliance Status",
                    "Executive Summary",
                ],
            )

        with col2:
            format_type = st.selectbox(
                "Export Format",
                ["PDF", "Excel", "HTML"],
            )

        # Generate Report Button
        generate = st.button("📊 Generate Report", type="primary", use_container_width=True)

        if generate:
            with st.spinner("Generating report... please wait ⏳"):
                result = self.report_generator.generate_report(report_type, format_type)

                # Check if report generated successfully
                if "✅" in result:
                    filepath = result.split(":")[-1].strip()

                    st.success(f"✅ {report_type} report generated successfully!")
                    st.markdown(f"**📁 Saved at:** `{filepath}`")

                    # Show actual download button
                    with open(filepath, "rb") as f:
                        file_bytes = f.read()

                        # Display PDF preview if PDF selected
                        if format_type == "PDF":
                            st.download_button(
                                label="⬇️ Download PDF Report",
                                data=file_bytes,
                                file_name=os.path.basename(filepath),
                                mime="application/pdf",
                            )

                            # Preview PDF in browser window
                            base64_pdf = f"data:application/pdf;base64,{file_bytes.decode('latin1')}"
                            st.markdown(
                                f'<iframe src="data:application/pdf;base64,{file_bytes.decode("latin1")}" '
                                f'width="100%" height="700px" type="application/pdf"></iframe>',
                                unsafe_allow_html=True,
                            )

                        elif format_type == "Excel":
                            st.download_button(
                                label="⬇️ Download Excel Report",
                                data=file_bytes,
                                file_name=os.path.basename(filepath),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )

                        elif format_type == "HTML":
                            st.download_button(
                                label="⬇️ Download HTML Report",
                                data=file_bytes,
                                file_name=os.path.basename(filepath),
                                mime="text/html",
                            )
                else:
                    st.error(result)

        # Recently generated reports
        st.divider()
        st.subheader("Recent Reports")

        reports = self.report_generator.get_generated_reports()
        if reports:
            df = pd.DataFrame(reports)
            st.dataframe(df[["name", "size", "created"]], use_container_width=True)
        else:
            st.info("No reports generated yet.")
    # -------------------------------------------------
    # VENDOR PORTAL
    # -------------------------------------------------
    def render_vendor_portal(self):
        st.markdown('<div class="main-header">🏢 Vendor Portal</div>', unsafe_allow_html=True)
        
        st.info("🚧 Vendor Portal module is under development")
        
        # Vendor information
        st.subheader("Vendor Self-Service Portal")
        
        tab1, tab2, tab3 = st.tabs(["📋 Profile Management", "📊 Performance", "📝 Documents"])
        
        with tab1:
            st.subheader("Vendor Profile")
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Company Name", "Vendor Corporation")
                st.text_input("Contact Person", "John Smith")
                st.text_input("Email", "john@vendorcorp.com")
                st.text_input("Phone", "+1-555-0123")
            
            with col2:
                st.text_area("Address", "123 Business Ave, Suite 100\nNew York, NY 10001")
                st.selectbox("Business Category", ["IT Services", "Logistics", "Manufacturing", "Consulting"])
                st.text_input("Tax ID", "12-3456789")
            
            if st.button("Update Profile"):
                st.success("Profile updated successfully!")
        
        with tab2:
            st.subheader("Performance Metrics")
            
            # Sample performance data
            perf_metrics = pd.DataFrame({
                'Metric': ['Quality Score', 'Delivery Performance', 'Cost Efficiency', 'Communication', 'Overall Rating'],
                'Score': [88, 92, 85, 90, 89],
                'Industry Average': [82, 85, 80, 83, 82],
                'Trend': ['↗️ Improving', '→ Stable', '↗️ Improving', '→ Stable', '↗️ Improving']
            })
            
            st.dataframe(perf_metrics, use_container_width=True)
            
            # Performance chart
            fig = px.bar(perf_metrics, x='Metric', y=['Score', 'Industry Average'], 
                        barmode='group', title='Performance vs Industry Average')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Document Management")
            
            documents = pd.DataFrame({
                'Document': ['Certificate of Insurance', 'W-9 Form', 'Quality Certifications', 'Compliance Documents'],
                'Status': ['✅ Approved', '✅ Approved', '🔄 Under Review', '✅ Approved'],
                'Last Updated': ['2024-02-15', '2024-01-20', '2024-03-01', '2024-02-28'],
                'Action': ['View/Download', 'View/Download', 'View/Download', 'View/Download']
            })
            
            st.dataframe(documents, use_container_width=True)
            
            st.file_uploader("Upload New Document", type=['pdf', 'doc', 'docx'])

    # -------------------------------------------------
    # SETTINGS
    # -------------------------------------------------
    def render_settings(self):
        st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)
        
        st.info("🚧 Settings module is under development")
        
        tab1, tab2, tab3 = st.tabs(["User Preferences", "System Settings", "Data Management"])
        
        with tab1:
            st.subheader("User Preferences")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.selectbox("Theme", ["Light", "Dark", "Auto"])
                st.selectbox("Language", ["English", "Spanish", "French", "German"])
                st.slider("Dashboard Refresh Rate (minutes)", 1, 60, 5)
            
            with col2:
                st.multiselect("Default Dashboard Views", 
                              ["Overview", "Performance", "Financial", "Risk", "Compliance"])
                st.checkbox("Email Notifications", value=True)
                st.checkbox("Desktop Notifications", value=False)
            
            if st.button("Save Preferences"):
                st.success("Preferences saved successfully!")
        
        with tab2:
            st.subheader("System Configuration")
            
            st.number_input("Performance Threshold (%)", 0, 100, 70)
            st.number_input("Risk Threshold (%)", 0, 100, 80)
            st.number_input("Auto-Archive Period (days)", 30, 365, 90)
            
            st.text_area("Email Templates", "Default email template content...", height=150)
            
            if st.button("Update System Settings"):
                st.success("System settings updated!")
        
        with tab3:
            st.subheader("Data Management")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.button("🔄 Refresh All Data", use_container_width=True)
                st.button("📤 Export All Data", use_container_width=True)
                st.button("🧹 Clear Cache", use_container_width=True)
            
            with col2:
                st.button("🔍 Data Quality Check", use_container_width=True)
                st.button("📊 Generate Data Report", use_container_width=True)
                st.button("🗑️ Archive Old Data", use_container_width=True)
            
            st.warning("⚠️ These actions may affect system performance")

    # -------------------------------------------------
    # MAIN RUN
    # -------------------------------------------------
    def run(self):
        self.render_sidebar()
        if st.session_state.user is None:
            st.warning("Please login to access the dashboard.")
            return

        nav_map = {
            "Overview Dashboard": self.render_overview_dashboard,
            "Vendor Performance": self.render_vendor_performance,
            "Financial Analytics": self.render_financial_analytics,
            "Brand & ESG Analytics": self.render_brand_esg_analytics,
            "Risk Management": self.render_risk_management,
            "Compliance": self.render_compliance,
            "Reports": self.render_reports,
            "Vendor Portal": self.render_vendor_portal,
            "Settings": self.render_settings
        }
        selected = st.session_state.get("selected_nav", "Overview Dashboard")
        nav_map.get(selected, self.render_overview_dashboard)()


# -------------------------------------------------
# APP ENTRY POINT
# -------------------------------------------------
if __name__ == "__main__":
    dashboard = VendorDashboard()
    dashboard.run()