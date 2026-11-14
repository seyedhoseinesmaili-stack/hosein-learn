from django.contrib import admin
from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from main.models import (
    Course,
    CourseVideo,
    Profile,
    UserCourseProgress,
    UserVideoProgress,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "phone", "created_at")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    list_editable = ("is_active",)


@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "duration_seconds", "order", "video_file")
    list_filter = ("course",)
    search_fields = ("title", "course__title")


@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "completed_videos_display",
        "progress_display",
        "watched_time_display",
        "updated_at",
    )
    list_filter = ("course",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "course__title")

    def get_queryset(self, request):
        watched_time = (
            UserVideoProgress.objects.filter(
                user_id=OuterRef("user_id"),
                video__course_id=OuterRef("course_id"),
            )
            .order_by()
            .values("user_id")
            .annotate(total=Sum("watched_seconds"))
            .values("total")[:1]
        )
        return (
            super()
            .get_queryset(request)
            .select_related("user", "course")
            .annotate(
                total_videos=Count("course__videos", distinct=True),
                completed_count=Count("completed_videos", distinct=True),
                watched_seconds=Coalesce(
                    Subquery(watched_time, output_field=IntegerField()),
                    Value(0),
                ),
            )
        )

    @admin.display(description="ویدیوهای تکمیل‌شده")
    def completed_videos_display(self, obj):
        return f"{obj.completed_count} از {obj.total_videos}"

    @admin.display(description="پیشرفت")
    def progress_display(self, obj):
        if not obj.total_videos:
            return "۰٪"
        return f"{int(obj.completed_count * 100 / obj.total_videos)}٪"

    @admin.display(description="زمان تماشا", ordering="watched_seconds")
    def watched_time_display(self, obj):
        hours, remainder = divmod(obj.watched_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"


@admin.register(UserVideoProgress)
class UserVideoProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "course_title", "video", "watched_time_display", "updated_at")
    list_filter = ("video__course",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "video__title")
    list_select_related = ("user", "video", "video__course")

    @admin.display(description="دوره", ordering="video__course__title")
    def course_title(self, obj):
        return obj.video.course.title

    @admin.display(description="زمان تماشا", ordering="watched_seconds")
    def watched_time_display(self, obj):
        hours, remainder = divmod(obj.watched_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"