import mimetypes
import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, F, Sum
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

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


@login_required(login_url="/login/")
@require_http_methods(["GET", "HEAD"])
def video_stream(request, video_id):
    video = get_object_or_404(
        CourseVideo.objects.filter(course__is_active=True),
        pk=video_id,
    )
    if not video.has_local_file or not video.video_file.storage.exists(video.video_file.name):
        return HttpResponse(status=404)

    file_size = video.video_file.size
    start = 0
    end = file_size - 1
    status_code = 200
    range_header = request.headers.get("Range")

    if range_header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match or (not match.group(1) and not match.group(2)):
            match = None

        if match:
            first, last = match.groups()
            try:
                if first:
                    start = int(first)
                    end = int(last) if last else file_size - 1
                else:
                    suffix_length = int(last)
                    if suffix_length > 0:
                        start = max(file_size - suffix_length, 0)
                        end = file_size - 1
                    else:
                        start = file_size
            except ValueError:
                start = file_size

            if start >= file_size or end < start:
                response = HttpResponse(status=416)
                response["Content-Range"] = f"bytes */{file_size}"
                response["Accept-Ranges"] = "bytes"
                return response

            end = min(end, file_size - 1)
            status_code = 206
        else:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{file_size}"
            response["Accept-Ranges"] = "bytes"
            return response

    content_length = max(end - start + 1, 0)
    content_type = mimetypes.guess_type(video.video_file.name)[0] or "application/octet-stream"
    response = HttpResponse(status=status_code) if request.method == "HEAD" else StreamingHttpResponse(
        stream_video_file(video.video_file, start, content_length),
        status=status_code,
        content_type=content_type,
    )
    response["Accept-Ranges"] = "bytes"
    response["Content-Length"] = str(content_length)
    response["Cache-Control"] = "private, no-store"
    if status_code == 206:
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    return response


def stream_video_file(video_file, start, length):
    with video_file.open("rb") as source:
        source.seek(start)
        remaining = length
        while remaining:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def logout_view(request):
    logout(request)
    return redirect("home")

