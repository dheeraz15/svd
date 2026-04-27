from django.urls import path
from . import views

urlpatterns = [
    path("",              views.gallery,          name="gallery"),
    path("viewer/",       views.viewer,           name="viewer"),
    path("api/original/", views.original_image,   name="original_image"),
    path("api/compressed/", views.compressed_image, name="compressed_image"),
]
