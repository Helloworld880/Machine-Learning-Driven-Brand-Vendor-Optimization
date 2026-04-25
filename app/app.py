import requests
import streamlit as st

from config.settings import get_settings


settings = get_settings()


def _api_get(path: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{settings.API_BASE_URL}{path}", headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def _login(username: str, password: str) -> str | None:
    response = requests.post(
        f"{settings.API_BASE_URL}/api/v1/login",
        data={"username": username, "password": password},
        timeout=20,
    )
    if response.status_code != 200:
        return None
    return response.json().get("access_token")


def main():
    st.set_page_config(page_title="Vendor Insight 360", layout="wide")
    st.title("Vendor Insight 360 - API Driven Frontend")

    if "token" not in st.session_state:
        st.session_state.token = None

    if not st.session_state.token:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            token = _login(username, password)
            if token:
                st.session_state.token = token
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid credentials or API unavailable.")
        return

    st.success("Connected to backend API")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Vendor KPIs")
        try:
            vendors = _api_get("/api/v1/vendors?page=1&limit=20", st.session_state.token)
            st.dataframe(vendors.get("data", []), use_container_width=True)
        except Exception as exc:
            st.error(f"Failed to fetch vendors: {exc}")

    with col2:
        st.subheader("Vendor Leaderboard")
        try:
            performance = _api_get("/api/v1/vendors/performance?page=1&limit=20", st.session_state.token)
            rows = performance.get("data", [])
            st.dataframe(rows, use_container_width=True)
            low_perf = [v for v in rows if v.get("alert") == "low_performance_alert"]
            st.metric("Low Performance Alerts", len(low_perf))
        except Exception as exc:
            st.error(f"Failed to fetch performance data: {exc}")

    if st.button("Logout"):
        st.session_state.token = None
        st.rerun()


if __name__ == "__main__":
    main()
