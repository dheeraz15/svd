"""
SVD image compression using only numpy for all matrix math.

Each RGB channel is treated as an independent 2D matrix.  We decompose it
with numpy.linalg.svd and reconstruct using only the top-k singular values,
giving a rank-k approximation of the channel.

Large images are resized to MAX_SVD_DIMENSION pixels on the longest side
before decomposition so the page stays interactive.
"""

import numpy as np
import cv2

MAX_SVD_DIMENSION = 900  # pixels on the longest side before running SVD


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resize_for_svd(img_bgr):
    """Shrink so the longest side is at most MAX_SVD_DIMENSION."""
    h, w = img_bgr.shape[:2]
    if max(h, w) <= MAX_SVD_DIMENSION:
        return img_bgr
    scale = MAX_SVD_DIMENSION / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _compress_channel(channel: np.ndarray, k: int) -> np.ndarray:
    """Return the rank-k SVD reconstruction of a 2-D float array."""
    U, S, Vt = np.linalg.svd(channel, full_matrices=False)
    # Reconstruct: U[:, :k]  @  diag(S[:k])  @  Vt[:k, :]
    reconstructed = (U[:, :k] * S[:k]) @ Vt[:k, :]
    return np.clip(reconstructed, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_image_dimensions(image_path: str):
    """Return (height, width, max_k) for the SVD-sized version of the image."""
    img = cv2.imread(image_path)
    img = _resize_for_svd(img)
    h, w = img.shape[:2]
    return h, w, min(h, w)


def make_resized_jpeg(image_path: str) -> bytes:
    """Return the SVD-sized original as a JPEG (used in the left panel)."""
    img = cv2.imread(image_path)
    img = _resize_for_svd(img)
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return bytes(buf)


def make_compressed_jpeg(image_path: str, k: int) -> bytes:
    """
    Load the image, resize it, run rank-k SVD on each RGB channel,
    and return the result encoded as a JPEG.
    """
    img_bgr = cv2.imread(image_path)
    img_bgr = _resize_for_svd(img_bgr)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).astype(float)

    compressed_channels = [
        _compress_channel(img_rgb[:, :, c], k)
        for c in range(3)
    ]
    compressed_rgb = np.stack(compressed_channels, axis=2)
    compressed_bgr = cv2.cvtColor(compressed_rgb, cv2.COLOR_RGB2BGR)

    _, buf = cv2.imencode(".jpg", compressed_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return bytes(buf)


def estimate_svd_bytes(h: int, w: int, k: int) -> int:
    """
    Theoretical storage for a rank-k SVD of one m×n matrix:
      U  (h × k) + S  (k,) + Vt (k × w)  →  k*(h + 1 + w) float64 values

    Multiply by 3 channels and 8 bytes/float.
    """
    floats_per_channel = k * (h + 1 + w)
    return floats_per_channel * 3 * 8
