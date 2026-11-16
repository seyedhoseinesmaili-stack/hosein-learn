from django.urls import path
from .views import (
    course_detail,
    dashboard,
    home_view,
    log_in,
    logout_view,
    register,
    video_stream,
)

urlpatterns = [
    path("", home_view, name="home"),
    path("login/", log_in, name="login"),
    path("register/", register, name="register"),
    path("dashboard/", dashboard, name="dashboard"),
    path("course/<int:course_id>/", course_detail, name="course_detail"),
    path("video/<int:video_id>/stream/", video_stream, name="video_stream"),
    path("logout/", logout_view, name="logout"),
]