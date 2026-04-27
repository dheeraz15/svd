from pathlib import Path
from django.conf import settings


# Images are expected to already exist in media/images/.
# Add a new entry here whenever you drop a new image into that folder.
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


def images_dir() -> Path:
    return Path(settings.MEDIA_ROOT) / "images"


def original_path(image_id: str) -> Path:
    meta = get_image_meta(image_id)
    if meta is None:
        return images_dir() / f"{image_id}.jpg"
    return images_dir() / meta["filename"]


def get_image_meta(image_id: str):
    return next((img for img in IMAGE_LIBRARY if img["id"] == image_id), None)
