import uuid
from pathlib import Path
from django.conf import settings


IMAGE_LIBRARY = [
    {
        "id": "mona_lisa",
        "filename": "mona_lisa.jpg",
        "name": "Mona Lisa",
        "category": "Portrait",
        "description": "High-resolution museum scan of Leonardo da Vinci's Mona Lisa",
    },
    {
        "id": "africa_night",
        "filename": "BlackMarble_2016_1200m_africa_s_labeled.png",
        "name": "Africa at Night",
        "category": "Outdoor / Satellite",
        "description": "NASA Black Marble — Africa and the Arabian Peninsula at night, 2016",
    },
    {
        "id": "shot48",
        "filename": "Shot48.00498.png",
        "name": "Shot 48",
        "category": "Cartoon / Scene",
        "description": "High-resolution rendered scene",
    },
    {
        "id": "full_res",
        "filename": "full-res-for-display.png",
        "name": "Full Resolution",
        "category": "Landscape",
        "description": "Full-resolution display image",
    },
]

ALLOWED_UPLOAD_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def images_dir() -> Path:
    return Path(settings.MEDIA_ROOT) / "images"


def uploads_dir() -> Path:
    d = Path(settings.MEDIA_ROOT) / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def original_path(image_id: str) -> Path:
    meta = get_image_meta(image_id)

    if meta and not image_id.startswith("upload_"):
        return images_dir() / meta["filename"]

    # Scan uploads directory for a matching file (any extension)
    for ext in ALLOWED_UPLOAD_EXTENSIONS:
        p = uploads_dir() / f"{image_id}{ext}"
        if p.exists():
            return p

    return uploads_dir() / f"{image_id}.jpg"  # fallback (will 404 gracefully)


def get_image_meta(image_id: str):
    # Library images
    match = next((img for img in IMAGE_LIBRARY if img["id"] == image_id), None)
    if match:
        return match

    # Uploaded images — return minimal synthetic metadata
    if image_id.startswith("upload_"):
        return {
            "id": image_id,
            "name": "Uploaded Image",
            "category": "Upload",
            "description": "User-uploaded image",
        }

    return None


def save_upload(django_file) -> str:
    """Persist an uploaded InMemoryUploadedFile/TemporaryUploadedFile and return its image_id."""
    ext = Path(django_file.name).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        ext = ".jpg"

    image_id = f"upload_{uuid.uuid4().hex[:16]}"
    dest = uploads_dir() / f"{image_id}{ext}"

    with open(dest, "wb") as f:
        for chunk in django_file.chunks():
            f.write(chunk)

    return image_id
