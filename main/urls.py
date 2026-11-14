from django.urls import path
from .views import course_detail, dashboard, home_view, log_in, logout_view, register

urlpatterns = [
    path("", home_view, name="home"),
    path("login/", log_in, name="login"),
    path("register/", register, name="register"),
    path("dashboard/", dashboard, name="dashboard"),
    path("course/<int:course_id>/", course_detail, name="course_detail"),
    path("logout/", logout_view, name="logout"),
]