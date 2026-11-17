import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Course, CourseVideo, UserCourseProgress, UserVideoProgress


class HomePageTests(TestCase):
    def test_registration_does_not_require_terms_checkbox(self):
        response = self.client.get("/register/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "قوانین را می‌پذیرم")
        self.assertNotContains(response, 'id="agree"')

    def test_home_shows_only_active_courses_and_real_student_count(self):
        User.objects.create_user(username="student", password="pass123")
        User.objects.create_user(username="admin", password="pass123", is_staff=True)
        active_course = Course.objects.create(
            title="دوره فعال",
            description="معرفی دوره فعال",
        )
        inactive_course = Course.objects.create(
            title="دوره غیرفعال",
            description="این دوره نباید نمایش داده شود",
            is_active=False,
        )
        video = CourseVideo.objects.create(
            course=active_course,
            title="ویدیوی خصوصی",
            video_url="https://www.youtube.com/watch?v=example",
        )

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "آکادمی سید")
        self.assertContains(response, active_course.title)
        self.assertNotContains(response, inactive_course.title)
        self.assertNotContains(response, video.title)
        self.assertNotContains(response, video.video_url)
        self.assertEqual(response.context["courses_count"], 1)
        self.assertEqual(response.context["students_count"], 1)
        self.assertEqual(response.context["courses"][0], active_course)


class DashboardProgressTests(TestCase):
    def test_progress_and_study_time_follow_completed_video_durations(self):
        student = User.objects.create_user(username="learner", password="pass123")
        course = Course.objects.create(title="دوره آزمایشی")
        watched_video = CourseVideo.objects.create(
            course=course,
            title="ویدیوی اول",
            video_url="https://youtu.be/example",
            duration_seconds=3600,
            order=1,
        )
        next_video = CourseVideo.objects.create(
            course=course,
            title="ویدیوی دوم",
            video_url="https://youtu.be/example2",
            order=2,
        )
        progress = UserCourseProgress.objects.create(user=student, course=course)
        progress.completed_videos.add(watched_video)
        UserVideoProgress.objects.create(
            user=student,
            video=watched_video,
            watched_seconds=3690,
        )
        self.client.force_login(student)

        course_page = self.client.get(reverse("course_detail", args=[course.id]))
        self.assertEqual(course_page.status_code, 200)
        self.assertContains(course_page, "youtube-player")

        dashboard = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard.context["progress"], 50)
        self.assertEqual(dashboard.context["watched_hours"], 1)
        self.assertEqual(dashboard.context["watched_minutes"], 1)
        self.assertEqual(dashboard.context["watched_seconds_remainder"], 30)
        self.assertContains(dashboard, "آکادمی سید")

        watch_response = self.client.post(
            reverse("course_detail", args=[course.id]),
            {
                "action": "watch_time",
                "video_id": next_video.id,
                "watched_seconds": "15",
            },
        )
        self.assertEqual(watch_response.status_code, 200)
        self.assertEqual(watch_response.json()["watched_seconds"], 15)

        response = self.client.post(
            reverse("course_detail", args=[course.id]),
            {
                "action": "complete",
                "video_id": next_video.id,
                "duration_seconds": "1800",
            },
        )
        self.assertRedirects(response, reverse("course_detail", args=[course.id]))

        dashboard = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard.context["progress"], 100)
        self.assertEqual(dashboard.context["watched_hours"], 1)
        self.assertEqual(dashboard.context["watched_minutes"], 1)
        self.assertEqual(dashboard.context["watched_seconds_remainder"], 45)
        self.assertEqual(dashboard.context["watched_seconds"], 3705)
        next_video.refresh_from_db()
        self.assertEqual(next_video.duration_seconds, 1800)


class AdminWatchReportTests(TestCase):
    def test_admin_can_view_course_and_video_watch_reports(self):
        admin_user = User.objects.create_superuser(
            username="siteadmin",
            email="admin@example.com",
            password="pass123",
        )
        student = User.objects.create_user(username="learner", password="pass123")
        course = Course.objects.create(title="دوره گزارش")
        video = CourseVideo.objects.create(course=course, title="جلسه اول")
        UserCourseProgress.objects.create(user=student, course=course)
        UserVideoProgress.objects.create(user=student, video=video, watched_seconds=3723)
        self.client.force_login(admin_user)

        course_report = self.client.get(reverse("admin:main_usercourseprogress_changelist"))
        self.assertEqual(course_report.status_code, 200)
        self.assertContains(course_report, student.username)
        self.assertContains(course_report, "01:02:03")

        video_report = self.client.get(reverse("admin:main_uservideoprogress_changelist"))
        self.assertEqual(video_report.status_code, 200)
        self.assertContains(video_report, course.title)
        self.assertContains(video_report, video.title)


class AdminVideoUploadTests(TestCase):
    def test_video_form_uses_academy_brand_and_upload_progress_script(self):
        admin_user = User.objects.create_superuser(
            username="siteadmin",
            email="admin@example.com",
            password="pass123",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:main_coursevideo_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "پنل مدیریت آکادمی سید")
        self.assertContains(response, "main/admin-video-upload.js")


class VideoStreamTests(TestCase):
    def test_course_page_shows_message_when_video_file_is_missing(self):
        user = User.objects.create_user(username="learner", password="pass123")
        course = Course.objects.create(title="دوره ویدیو")
        self.client.force_login(user)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                video = CourseVideo.objects.create(
                    course=course,
                    title="ویدیوی گم‌شده",
                    video_file="course_videos/missing.mp4",
                )
                response = self.client.get(reverse("course_detail", args=[course.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "فایل این ویدیو روی سرور پیدا نشد")
        self.assertNotContains(response, f'data-video-id="{video.id}"')

    def test_video_stream_supports_byte_ranges_when_debug_is_disabled(self):
        user = User.objects.create_user(username="learner", password="pass123")
        course = Course.objects.create(title="دوره ویدیو")
        self.client.force_login(user)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root, DEBUG=False):
                video = CourseVideo.objects.create(
                    course=course,
                    title="ویدیوی نمونه",
                    video_file=SimpleUploadedFile("sample.mp4", b"0123456789"),
                )
                response = self.client.get(
                    reverse("video_stream", args=[video.id]),
                    HTTP_RANGE="bytes=3-6",
                )
                body = b"".join(response.streaming_content)

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Content-Range"], "bytes 3-6/10")
        self.assertEqual(body, b"3456")

    def test_video_stream_rejects_unsatisfiable_ranges(self):
        user = User.objects.create_user(username="learner", password="pass123")
        course = Course.objects.create(title="دوره ویدیو")
        self.client.force_login(user)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root, DEBUG=False):
                video = CourseVideo.objects.create(
                    course=course,
                    title="ویدیوی نمونه",
                    video_file=SimpleUploadedFile("sample.mp4", b"0123456789"),
                )
                response = self.client.get(
                    reverse("video_stream", args=[video.id]),
                    HTTP_RANGE="bytes=10-",
                )

        self.assertEqual(response.status_code, 416)
        self.assertEqual(response["Content-Range"], "bytes */10")


class LogoutTests(TestCase):
    def test_logout_redirects_to_home(self):
        user = User.objects.create_user(username="learner", password="pass123")
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)
