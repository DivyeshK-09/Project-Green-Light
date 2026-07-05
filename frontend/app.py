"""
frontend/app.py

Streamlit dashboard for Project Green Light.

IMPORTANT: this file never imports from backend/. All communication
happens over REST so frontend and backend can be deployed, scaled,
or replaced independently.

No login screen in this phase -- single-user offline desktop app,
straight to the dashboard.
"""

import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Project Green Light", page_icon="🟢", layout="wide")


def api_get(path: str, **kwargs):
    return requests.get(f"{API_BASE_URL}{path}", timeout=15, **kwargs)


def api_post(path: str, **kwargs):
    return requests.post(f"{API_BASE_URL}{path}", timeout=30, **kwargs)


def api_delete(path: str, **kwargs):
    return requests.delete(f"{API_BASE_URL}{path}", timeout=15, **kwargs)


# ---------------------------------------------------------------------------
# Upload + process
# ---------------------------------------------------------------------------

def render_upload_section():
    st.subheader("📤 Upload Image")

    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "bmp", "webp"])

    if uploaded_file is not None:
        col_preview, col_action = st.columns([2, 1])

        with col_preview:
            st.image(uploaded_file, caption="Preview", width=350)

        with col_action:
            if st.button("Process Image", type="primary", use_container_width=True):
                with st.spinner("Uploading and processing..."):
                    try:
                        upload_response = api_post(
                            "/records/upload",
                            files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                        )
                    except requests.exceptions.ConnectionError:
                        st.error("Could not reach the backend. Is the FastAPI server running on port 8000?")
                        return

                    if upload_response.status_code != 200:
                        st.error(f"Upload failed: {upload_response.text}")
                        return

                    record_id = upload_response.json()["id"]
                    process_response = api_post(f"/records/{record_id}/process")

                    if process_response.status_code != 200:
                        st.error(f"Processing failed: {process_response.text}")
                        return

                    st.session_state["last_result"] = process_response.json()
                    st.rerun()

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        st.markdown("#### Results")
        m1, m2, m3 = st.columns(3)
        m1.metric("Brightness", result.get("brightness"))
        m2.metric("Blur (Laplacian variance)", result.get("blur"))
        m3.metric("Recommendation", result.get("output"))


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def render_history_section():
    st.subheader("🕘 History")

    try:
        response = api_get("/records/history")
    except requests.exceptions.ConnectionError:
        st.error("Could not reach the backend. Is the FastAPI server running on port 8000?")
        return

    if response.status_code != 200:
        st.error("Could not load history.")
        return

    records = response.json()["records"]
    if not records:
        st.info("No records yet. Upload an image to get started.")
        return

    for record in records:
        with st.container(border=True):
            cols = st.columns([1, 2, 1])

            with cols[0]:
                st.image(f"{API_BASE_URL}{record['image_path']}", width=140)

            with cols[1]:
                st.write(f"**Timestamp:** {record['timestamp']}")
                st.write(f"**Brightness:** {record.get('brightness', '—')}")
                st.write(f"**Blur:** {record.get('blur', '—')}")
                st.write(f"**Recommendation:** {record.get('output', 'Not processed yet')}")

            with cols[2]:
                if st.button("Delete", key=f"delete_{record['id']}"):
                    delete_response = api_delete(f"/records/{record['id']}")
                    if delete_response.status_code == 200:
                        st.rerun()
                    else:
                        st.error("Delete failed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

st.title("🟢 Project Green Light")
st.caption("Monitoring & Recommendation Dashboard — Phase 1: functional pipeline. Recommendation logic is a placeholder until deployment rules are finalized.")

render_upload_section()
st.divider()
render_history_section()
