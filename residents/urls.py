from django.urls import path
from . import views

app_name = "residents"
urlpatterns = [
    path("request/", views.request_access_code, name="request_access_code"),
    path("verify/", views.verify_access_code, name="verify_code"),
    # staff-only routes
    path("residents/add/", views.add_resident, name="add_resident"),
    path(
        "residents/upload-csv/", views.upload_residents_csv, name="upload_residents_csv"
    ),
]
