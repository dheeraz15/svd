from django.http import HttpResponse, Http404
from django.shortcuts import render

from .image_library import IMAGE_LIBRARY, get_image_meta, original_path
from .svd_compression import (
    get_image_dimensions,
    make_resized_jpeg,
    make_compressed_jpeg,
    estimate_svd_bytes,
)


def gallery(request):
    images = []
    for meta in IMAGE_LIBRARY:
        path = original_path(meta["id"])
        images.append({
            **meta,
            "available": path.exists(),
            "file_size": path.stat().st_size if path.exists() else 0,
            "file_size_mb": round(path.stat().st_size / 1_048_576, 1) if path.exists() else 0,
        })
    return render(request, "compressor/gallery.html", {"images": images})


def viewer(request):
    image_id = request.GET.get("image_id", IMAGE_LIBRARY[0]["id"])
    quality = max(1, min(100, int(request.GET.get("quality", 50))))

    meta = get_image_meta(image_id)
    if not meta:
        raise Http404("Unknown image")

    path = original_path(image_id)
    if not path.exists():
        raise Http404("Image not downloaded yet — check server console")

    h, w, max_k = get_image_dimensions(str(path))
    k = max(1, round(quality / 100 * max_k))

    original_bytes = path.stat().st_size
    svd_bytes = estimate_svd_bytes(h, w, k)

    context = {
        "meta": meta,
        "all_images": IMAGE_LIBRARY,
        "quality": quality,
        "k": k,
        "max_k": max_k,
        "width": w,
        "height": h,
        "original_mb": round(original_bytes / 1_048_576, 2),
        "svd_mb": round(svd_bytes / 1_048_576, 2),
        "compression_ratio": round(original_bytes / svd_bytes, 1) if svd_bytes else "—",
    }
    return render(request, "compressor/viewer.html", context)


def original_image(request):
    """Serve the SVD-resized original as JPEG (left panel reference)."""
    image_id = request.GET.get("image_id", "")
    meta = get_image_meta(image_id)
    if not meta:
        raise Http404("Unknown image")

    path = original_path(image_id)
    if not path.exists():
        raise Http404("Image not downloaded yet")

    jpeg = make_resized_jpeg(str(path))
    return HttpResponse(jpeg, content_type="image/jpeg")


def compressed_image(request):
    """Run SVD compression and return the result as JPEG (right panel).

    Accepts either ?quality=1-100 or ?k=N directly (used by the animator).
    """
    image_id = request.GET.get("image_id", "")
    quality = max(1, min(100, int(request.GET.get("quality", 50))))
    k_param = request.GET.get("k")

    meta = get_image_meta(image_id)
    if not meta:
        raise Http404("Unknown image")

    path = original_path(image_id)
    if not path.exists():
        raise Http404("Image not downloaded yet")

    _, _, max_k = get_image_dimensions(str(path))

    if k_param is not None:
        k = max(1, min(max_k, int(k_param)))
    else:
        k = max(1, round(quality / 100 * max_k))

    jpeg = make_compressed_jpeg(str(path), k)

    response = HttpResponse(jpeg, content_type="image/jpeg")
    # Expose these so JavaScript can read them without a separate API call
    response["X-Compressed-Bytes"] = len(jpeg)
    response["X-K"] = k
    response["X-Max-K"] = max_k
    response["Access-Control-Expose-Headers"] = "X-Compressed-Bytes, X-K, X-Max-K"
    return response
