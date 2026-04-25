import os
from pathlib import Path

import streamlit as st


def _upsert_env_values(updates: dict[str, str]) -> Path:
    env_path = Path(".env")
    existing: dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            existing[key.strip()] = value.strip()

    existing.update({k: str(v) for k, v in updates.items()})
    body = "\n".join(f"{key}={value}" for key, value in sorted(existing.items()))
    env_path.write_text(f"{body}\n", encoding="utf-8")
    return env_path


def render_settings(dashboard):
    st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)

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
        st.number_input("Performance Alert Threshold (%)", 0, 100, st.session_state.perf_threshold)
        st.number_input("High Risk Score Threshold (%)", 0, 100, 65)
        st.number_input("Churn Probability Threshold", 0.0, 1.0, 0.5, 0.05)
        st.number_input("Report Auto-Archive (days)", 30, 365, 90)
        st.caption(
            f"Configured demo login: `{dashboard.config.DEMO_ADMIN_USERNAME}` | "
            f"Session timeout: `{dashboard.config.SESSION_TIMEOUT_MINUTES}` minutes"
        )
        if st.button("💾 Update Config"):
            st.success("System config updated!")

        st.divider()
        st.subheader("Email & SMTP")
        st.caption("Configure SMTP for dashboard alert emails.")
        with st.form("email_settings_form"):
            e1, e2 = st.columns(2)
            smtp_host = e1.text_input("SMTP Host", value=str(getattr(dashboard.config, "EMAIL_HOST", "smtp.gmail.com")))
            smtp_port = e2.number_input("SMTP Port", min_value=1, max_value=65535, value=int(getattr(dashboard.config, "EMAIL_PORT", 587)), step=1)
            smtp_user = e1.text_input("SMTP Username", value=str(getattr(dashboard.config, "EMAIL_USER", "")))
            smtp_password = e2.text_input("SMTP Password / App Password", value=str(getattr(dashboard.config, "EMAIL_PASSWORD", "")), type="password")
            admin_email = st.text_input("Alert Recipient (Admin Email)", value=str(getattr(dashboard.config, "DEMO_ADMIN_EMAIL", "admin@company.com")))
            save_email = st.form_submit_button("💾 Save Email Settings", type="primary")

            if save_email:
                if not smtp_host.strip():
                    st.error("SMTP host is required.")
                elif not admin_email.strip():
                    st.error("Admin email is required.")
                else:
                    updates = {
                        "EMAIL_HOST": smtp_host.strip(),
                        "EMAIL_PORT": str(int(smtp_port)),
                        "EMAIL_USER": smtp_user.strip(),
                        "EMAIL_PASSWORD": smtp_password,
                        "DEMO_ADMIN_EMAIL": admin_email.strip(),
                    }
                    env_path = _upsert_env_values(updates)

                    for key, value in updates.items():
                        os.environ[key] = value
                        setattr(dashboard.config, key, int(value) if key == "EMAIL_PORT" else value)
                        if hasattr(dashboard, "email_service") and getattr(dashboard, "email_service", None):
                            setattr(dashboard.email_service.config, key, int(value) if key == "EMAIL_PORT" else value)

                    st.success(f"Email settings saved to {env_path}. New values are active now.")
                    st.caption("Restarting the app is recommended to ensure all modules pick up the new environment.")

    with tab3:
        st.subheader("Data Management")
        c1, c2, c3 = st.columns(3)
        if c1.button("🔄 Re-seed Database", use_container_width=True):
            with st.spinner("Seeding…"):
                dashboard.db._seed_all()
            st.success("Database re-seeded!")
        if c2.button("🤖 Retrain ML Models", use_container_width=True):
            if dashboard.ml:
                with st.spinner("Retraining…"):
                    dashboard.ml.retrain()
                st.success("Models retrained!")
            else:
                st.warning("ML engine not available.")
        if c3.button("🧹 Clear Reports Folder", use_container_width=True):
            import glob

            for file_path in glob.glob("reports/*"):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            st.success("Reports cleared!")

        st.divider()
        st.subheader("Dataset Upload")
        inventory = dashboard._dataset_inventory()
        if not inventory.empty:
            st.dataframe(inventory, use_container_width=True)

        uploaded = st.file_uploader(
            "Upload a CSV into the Data layer",
            type=["csv"],
            key="dataset_upload",
            help="Use this to replace or add datasets like vendors.csv, performance.csv, risk_history.csv, compliance_history.csv, or vendor_outcomes.csv.",
        )
        target_name = st.text_input(
            "Target file name",
            value="vendors.csv",
            help="Example: vendors.csv, performance.csv, risk_history.csv",
        )
        if st.button("📤 Save uploaded dataset", type="primary", use_container_width=True):
            if uploaded is None:
                st.warning("Choose a CSV file first.")
            elif not target_name.lower().endswith(".csv"):
                st.warning("Target file name must end with .csv")
            else:
                path = dashboard._save_uploaded_dataset(uploaded, target_name)
                st.success(f"Dataset saved to {path}")

        st.warning("⚠️ Re-seeding replaces all demo data. This cannot be undone.")

