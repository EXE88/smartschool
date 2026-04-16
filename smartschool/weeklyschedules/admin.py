from django.contrib import admin

from .models import WeeklySchedule


@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "classobj", "weekday", "period_1", "period_2", "period_3", "period_4")
    list_filter = ("weekday", "classobj")
    search_fields = ("classobj__name",)
    autocomplete_fields = ("classobj", "period_1", "period_2", "period_3", "period_4")
    list_select_related = ("classobj", "period_1", "period_2", "period_3", "period_4")
    ordering = ("classobj__name", "weekday")
