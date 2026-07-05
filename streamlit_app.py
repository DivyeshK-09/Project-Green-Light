import streamlit as st

from backend.database import get_connection, init_db, row_to_dict
from backend.rule_engine import get_recommendation
from backend.utils import compute_metrics, generate_unique_filename, is_allowed_image
from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parent / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Project Green Light", page_icon="🟢", layout="wide")

init_db()  # safe to call every run; no-ops if tables already exist


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
                if not is_allowed_image(uploaded_file.name):
                    st.error("Unsupported file type.")
                    return

                unique_filename = generate_unique_filename(uploaded_file.name)
                destination = UPLOAD_DIR / unique_filename
                with open(destination, "wb") as out_file:
                    out_file.write(uploaded_file.getvalue())

                with st.spinner("Processing..."):
                    with get_connection() as conn:
                        cursor = conn.execute(
                            """
                            INSERT INTO records (filename, original_filename, image_path, processed)
                            VALUES (?, ?, ?, 0)
                            """,
                            (unique_filename, uploaded_file.name, str(destination)),
                        )
                        record_id = cursor.lastrowid

                    try:
                        metrics = compute_metrics(str(destination))
                    except ValueError as exc:
                        st.error(str(exc))
                        return

                    recommendation = get_recommendation(
                        image_path=str(destination),
                        brightness=metrics["brightness"],
                        blur=metrics["blur"],
                    )

                    with get_connection() as conn:
                        conn.execute(
                            """
                            UPDATE records
                            SET brightness = ?, blur = ?, output = ?, processed = 1
                            WHERE id = ?
                            """,
                            (metrics["brightness"], metrics["blur"], recommendation, record_id),
                        )

                st.session_state["last_result"] = {
                    "brightness": metrics["brightness"],
                    "blur": metrics["blur"],
                    "output": recommendation,
                }
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

    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM records ORDER BY timestamp DESC").fetchall()

    if not rows:
        st.info("No records yet. Upload an image to get started.")
        return

    for row in rows:
        record = row_to_dict(row)
        with st.container(border=True):
            cols = st.columns([1, 2, 1])

            with cols[0]:
                image_path = Path(record["image_path"])
                if image_path.exists():
                    st.image(str(image_path), width=140)
                else:
                    st.caption("Image missing")

            with cols[1]:
                st.write(f"**Timestamp:** {record['timestamp']}")
                st.write(f"**Brightness:** {record.get('brightness', '—')}")
                st.write(f"**Blur:** {record.get('blur', '—')}")
                st.write(f"**Recommendation:** {record.get('output') or 'Not processed yet'}")

            with cols[2]:
                if st.button("Delete", key=f"delete_{record['id']}"):
                    with get_connection() as conn:
                        conn.execute("DELETE FROM records WHERE id = ?", (record["id"],))
                    image_path = Path(record["image_path"])
                    if image_path.exists():
                        image_path.unlink()
                    st.rerun()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

st.title("🟢 Project Green Light")
st.caption(
    "Monitoring & Recommendation Dashboard — Phase 1: functional pipeline. "
    "Recommendation logic is a placeholder until deployment rules are finalized."
)
st.caption("⚠️ Cloud demo: storage is ephemeral and resets on app restart.")

render_upload_section()
st.divider()
render_history_section()
