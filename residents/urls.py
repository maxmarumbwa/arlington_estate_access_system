from django.urls import path
from . import views

app_name = "residents"
urlpatterns = [
    path("request/", views.request_access_code, name="request_access_code"),
    path("verify/", views.verify_access_code, name="verify_code"),
]
