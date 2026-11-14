from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_progress_for_user(self, user):
        progress, _ = UserCourseProgress.objects.get_or_create(user=user, course=self)
        return progress.progress_percent()


class CourseVideo(models.Model):
    course = models.ForeignKey(Course, related_name="videos", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to="course_videos/", blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0, verbose_name="مدت زمان (ثانیه)")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def has_local_file(self):
        return bool(self.video_file and self.video_file.name)

    @property
    def embed_url(self):
        if self.has_local_file:
            return self.video_file.url

        url = self.video_url or ""
        if "youtube.com/watch?v=" in url:
            video_id = url.split("v=")[-1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[-1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return url


class UserCourseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="course_progress")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="user_progress")
    completed_videos = models.ManyToManyField(CourseVideo, blank=True, related_name="completed_by_users")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "course")
        ordering = ["-updated_at"]
        verbose_name = "پیشرفت دوره دانشجو"
        verbose_name_plural = "گزارش پیشرفت دوره دانشجویان"

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

    def progress_percent(self):
        total = self.course.videos.count()
        if total == 0:
            return 0
        completed = self.completed_videos.count()
        return int((completed / total) * 100)


class UserVideoProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="video_progress")
    video = models.ForeignKey(CourseVideo, on_delete=models.CASCADE, related_name="user_progress")
    watched_seconds = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "video")
        verbose_name = "زمان تماشای ویدیو"
        verbose_name_plural = "گزارش زمان تماشای ویدیوها"

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"
