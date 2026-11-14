from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, F, Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Course, CourseVideo, Profile, UserCourseProgress, UserVideoProgress


def home_view(request):
    courses = Course.objects.filter(is_active=True).annotate(video_count=Count("videos"))
    students_count = User.objects.filter(is_active=True, is_staff=False, is_superuser=False).count()
    return render(request, "main/home.html", {
        "courses": courses,
        "courses_count": courses.count(),
        "students_count": students_count,
    })


def log_in(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        return render(request, "main/login.html", {
            "error": "نام کاربری یا رمز عبور اشتباه است."
        })

    return render(request, "main/login.html")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if not username or not email or not password:
            return render(request, "main/register.html", {
                "error": "لطفاً همه‌ی فیلدها را پر کنید."
            })

        if password != confirm_password:
            return render(request, "main/register.html", {
                "error": "رمز عبور و تأیید آن یکسان نیستند."
            })

        if User.objects.filter(username=username).exists():
            return render(request, "main/register.html", {
                "error": "این نام کاربری قبلاً استفاده شده است."
            })

        if User.objects.filter(email=email).exists():
            return render(request, "main/register.html", {
                "error": "این ایمیل قبلاً ثبت شده است."
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        Profile.objects.get_or_create(user=user, defaults={"email": email})
        login(request, user)
        return redirect("dashboard")

    return render(request, "main/register.html")


@login_required(login_url="/login/")
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    courses = Course.objects.filter(is_active=True).prefetch_related("videos")
    course_data = []

    total_videos = 0
    completed_videos = 0
    for course in courses:
        progress_obj, _ = UserCourseProgress.objects.get_or_create(user=request.user, course=course)
        total_course_videos = course.videos.count()
        total_videos += total_course_videos
        done_count = progress_obj.completed_videos.count()
        completed_videos += done_count
        course_data.append({
            "course": course,
            "progress": progress_obj.progress_percent(),
            "completed_count": done_count,
            "total_count": total_course_videos,
        })

    overall_progress = 0
    if total_videos:
        overall_progress = int((completed_videos / total_videos) * 100)

    watched_seconds = UserVideoProgress.objects.filter(
        user=request.user,
        video__course__is_active=True,
    ).aggregate(total=Sum("watched_seconds"))["total"] or 0

    return render(request, "main/dashboard.html", {
        "user": request.user,
        "profile": profile,
        "courses": course_data,
        "courses_count": len(course_data),
        "progress": overall_progress,
        "watched_seconds": watched_seconds,
        "watched_hours": watched_seconds // 3600,
        "watched_minutes": (watched_seconds % 3600) // 60,
        "watched_seconds_remainder": watched_seconds % 60,
    })


@login_required(login_url="/login/")
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    progress_obj, _ = UserCourseProgress.objects.get_or_create(user=request.user, course=course)

    if request.method == "POST":
        action = request.POST.get("action", "complete")
        video_id = request.POST.get("video_id")
        if not video_id:
            return HttpResponseBadRequest("شناسه ویدیو ارسال نشده است.")

        video = get_object_or_404(course.videos, id=video_id)
        if action == "watch_time":
            try:
                watched_seconds = int(request.POST.get("watched_seconds", ""))
            except (TypeError, ValueError, OverflowError):
                return HttpResponseBadRequest("مدت تماشای ارسال‌شده معتبر نیست.")
            if watched_seconds < 1 or watched_seconds > 20:
                return HttpResponseBadRequest("مدت هر گزارش تماشا باید بین ۱ تا ۲۰ ثانیه باشد.")
            watch_progress, _ = UserVideoProgress.objects.get_or_create(
                user=request.user,
                video=video,
            )
            UserVideoProgress.objects.filter(pk=watch_progress.pk).update(
                watched_seconds=F("watched_seconds") + watched_seconds,
            )
            watch_progress.refresh_from_db(fields=["watched_seconds"])
            return JsonResponse({"watched_seconds": watch_progress.watched_seconds})

        duration_value = request.POST.get("duration_seconds")
        if duration_value:
            try:
                duration_seconds = int(float(duration_value))
            except (TypeError, ValueError, OverflowError):
                return HttpResponseBadRequest("مدت زمان ویدیو معتبر نیست.")
            if duration_seconds < 1 or duration_seconds > 86400:
                return HttpResponseBadRequest("مدت زمان ویدیو باید بین ۱ ثانیه و ۲۴ ساعت باشد.")
            if video.duration_seconds == 0:
                video.duration_seconds = duration_seconds
                video.save(update_fields=["duration_seconds"])

        if action == "duration":
            return JsonResponse({"duration_seconds": video.duration_seconds})
        if action != "complete":
            return HttpResponseBadRequest("عملیات درخواست‌شده معتبر نیست.")

        if action == "complete":
            progress_obj.completed_videos.add(video)
        return redirect("course_detail", course_id=course.id)

    return render(request, "main/course_detail.html", {
        "course": course,
        "progress": progress_obj.progress_percent(),
        "completed_videos": progress_obj.completed_videos.all(),
        "videos": course.videos.all(),
    })


def logout_view(request):
    logout(request)
    return redirect("login")

