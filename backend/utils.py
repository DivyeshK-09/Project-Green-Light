"""
utils.py

Image processing helpers. Currently computes:
- Brightness (mean grayscale intensity, 0-255)
- Blur (variance of Laplacian; lower => blurrier)

These are cheap, deterministic quality signals used today as
placeholder metrics and, later, as candidate input features for
a trained model.
"""

import uuid
from pathlib import Path

import cv2
import numpy as np


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def is_allowed_image(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename: str) -> str:
    """Prevents overwrites by prefixing a UUID onto the original name."""
    suffix = Path(original_filename).suffix.lower() or ".jpg"
    safe_stem = Path(original_filename).stem.replace(" ", "_")[:40]
    return f"{uuid.uuid4().hex[:12]}_{safe_stem}{suffix}"


def load_image(image_path: str) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image at {image_path}. File may be corrupt or unsupported.")
    return image


def compute_brightness(image: np.ndarray) -> float:
    """Average grayscale intensity, 0 (black) - 255 (white)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def compute_blur(image: np.ndarray) -> float:
    """Variance of the Laplacian. Higher = sharper, lower = blurrier."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def compute_metrics(image_path: str) -> dict:
    image = load_image(image_path)
    return {
        "brightness": round(compute_brightness(image), 2),
        "blur": round(compute_blur(image), 2),
    }
