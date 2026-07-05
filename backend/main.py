"""
main.py

Responsible for:
- API routes (upload, process, history, delete)
- Wiring together database.py, utils.py, rule_engine.py
- Saving uploaded files with collision-safe names
- Returning clean JSON responses

Frontend never imports this module. All communication is REST.

No authentication in this phase -- this is a single-user, offline
desktop pipeline. If/when this needs to run somewhere multi-user or
networked, add auth back in as its own module rather than bolting
it onto every route.
"""

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.staticfiles import StaticFiles

from backend.database import get_connection, init_db, row_to_dict
from backend.models import (
    HistoryResponse,
    MessageResponse,
    RecordResponse,
    UploadResponse,
)
from backend.rule_engine import get_recommendation
from backend.utils import compute_metrics, generate_unique_filename, is_allowed_image

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Project Green Light API", version="0.1.0")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", response_model=MessageResponse)
def health_check():
    return {"message": "ok"}


# ---------------------------------------------------------------------------
# Records: upload -> process -> history -> delete
# ---------------------------------------------------------------------------

@app.post("/records/upload", response_model=UploadResponse)
def upload_image(file: UploadFile = File(...)):
    if not file.filename or not is_allowed_image(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: .jpg, .jpeg, .png, .bmp, .webp",
        )

    unique_filename = generate_unique_filename(file.filename)
    destination = UPLOAD_DIR / unique_filename

    with open(destination, "wb") as out_file:
        out_file.write(file.file.read())

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO records (filename, original_filename, image_path, processed)
            VALUES (?, ?, ?, 0)
            """,
            (unique_filename, file.filename, f"/uploads/{unique_filename}"),
        )
        record_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()

    record = row_to_dict(row)
    return {
        "id": record["id"],
        "filename": record["filename"],
        "image_path": record["image_path"],
        "timestamp": record["timestamp"],
        "processed": bool(record["processed"]),
    }


@app.post("/records/{record_id}/process", response_model=RecordResponse)
def process_image(record_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        record = row_to_dict(row)

    absolute_path = UPLOAD_DIR / record["filename"]
    if not absolute_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored image file is missing on disk")

    try:
        metrics = compute_metrics(str(absolute_path))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    recommendation = get_recommendation(
        image_path=str(absolute_path),
        brightness=metrics["brightness"],
        blur=metrics["blur"],
        camera_id=record.get("camera_id"),
        location=record.get("location"),
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
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()

    updated = row_to_dict(row)
    updated["processed"] = bool(updated["processed"])
    return updated


@app.get("/records/history", response_model=HistoryResponse)
def get_history():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM records ORDER BY timestamp DESC").fetchall()

    records = []
    for row in rows:
        record = row_to_dict(row)
        record["processed"] = bool(record["processed"])
        records.append(record)

    return {"total": len(records), "records": records}


@app.get("/records/{record_id}", response_model=RecordResponse)
def get_record(record_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    record = row_to_dict(row)
    record["processed"] = bool(record["processed"])
    return record


@app.delete("/records/{record_id}", response_model=MessageResponse)
def delete_record(record_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        record = row_to_dict(row)
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))

    image_file = UPLOAD_DIR / record["filename"]
    if image_file.exists():
        image_file.unlink()

    return {"message": f"Record {record_id} deleted"}
