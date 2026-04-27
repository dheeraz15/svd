from django.urls import path
from . import views

urlpatterns = [
    path("",                views.gallery,          name="gallery"),
    path("viewer/",         views.viewer,           name="viewer"),
    path("upload/",         views.upload_image,     name="upload_image"),
    path("api/original/",   views.original_image,   name="original_image"),
    path("api/compressed/", views.compressed_image, name="compressed_image"),
]
