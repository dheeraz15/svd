import cv2
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render

from .image_library import IMAGE_LIBRARY, get_image_meta, original_path, save_upload
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
        raise Http404("Image not found")

    h, w, max_k = get_image_dimensions(str(path))
    k = max(1, round(quality / 100 * max_k))

    original_bytes = path.stat().st_size
    svd_bytes = estimate_svd_bytes(h, w, k)

    is_upload = image_id.startswith("upload_")

    # Build switcher list: uploaded image goes first so it's visible in the tab strip
    all_images = IMAGE_LIBRARY.copy()
    if is_upload:
        all_images = [meta] + all_images

    context = {
        "meta": meta,
        "all_images": all_images,
        "is_upload": is_upload,
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
    image_id = request.GET.get("image_id", "")
    if not get_image_meta(image_id):
        raise Http404("Unknown image")

    path = original_path(image_id)
    if not path.exists():
        raise Http404("Image not found")

    jpeg = make_resized_jpeg(str(path))
    return HttpResponse(jpeg, content_type="image/jpeg")


def compressed_image(request):
    image_id = request.GET.get("image_id", "")
    quality = max(1, min(100, int(request.GET.get("quality", 50))))
    k_param = request.GET.get("k")

    if not get_image_meta(image_id):
        raise Http404("Unknown image")

    path = original_path(image_id)
    if not path.exists():
        raise Http404("Image not found")

    _, _, max_k = get_image_dimensions(str(path))

    if k_param is not None:
        k = max(1, min(max_k, int(k_param)))
    else:
        k = max(1, round(quality / 100 * max_k))

    jpeg = make_compressed_jpeg(str(path), k)

    response = HttpResponse(jpeg, content_type="image/jpeg")
    response["X-Compressed-Bytes"] = len(jpeg)
    response["X-K"] = k
    response["X-Max-K"] = max_k
    response["Access-Control-Expose-Headers"] = "X-Compressed-Bytes, X-K, X-Max-K"
    return response


def upload_image(request):
    """Accept a POST with an image file, save it, return JSON with the new image_id."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    file = request.FILES.get("image")
    if not file:
        return JsonResponse({"error": "No file attached (field name: image)"}, status=400)

    # Size guard: 200 MB max
    if file.size > 200 * 1024 * 1024:
        return JsonResponse({"error": "File too large (max 200 MB)"}, status=400)

    try:
        image_id = save_upload(file)
        path = original_path(image_id)

        # Validate the file is a readable image
        img = cv2.imread(str(path))
        if img is None:
            path.unlink(missing_ok=True)
            return JsonResponse({"error": "File could not be read as an image"}, status=400)

        h, w = img.shape[:2]
        size_mb = round(path.stat().st_size / 1_048_576, 2)

        return JsonResponse({
            "image_id": image_id,
            "width": w,
            "height": h,
            "size_mb": size_mb,
        })

    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
