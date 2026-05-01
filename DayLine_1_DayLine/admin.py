from django.contrib import admin

from .models import * 
# Register your models here.

# イベント
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "room",
        "title",
        "created_by",
        "start_date",
        "start_time",
        "end_date",
        "end_time",
        "allday",
        "repeat",
        "url",
        "location",
        "memo",
    )

    list_display_links = (
        "id",
        "title",
    )

    list_filter = (
        "room",
        "allday",
        "start_date",
    )

    search_fields = (
        "title",
        "room__room_name",
        "created_by__username",
    )

    ordering = (
        "-start_date",
        "-start_time",
    )

    autocomplete_fields = (
        "room",
        "created_by",
    )

# 色
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):

    list_display = ("color_name", "color")
    search_fields = ("color_name",)

# 繰り返し
@admin.register(Repeat)
class RepeatAdmin(admin.ModelAdmin):
    list_display = ("repeat_name", "repeat_code")
    search_fields = ("repeat_name",)


# ↓これ書くことで admin.site.register(Event, EventAdmin) を書かなくてよくなる
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "room_name",
        "owner",
        "is_personal",
        "join_url",
    )

    list_filter = ("is_personal",)

    search_fields = ("room_name", "owner__username")

    autocomplete_fields = ("owner",)

# Roomモデルを参照
class RoomAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "room_name",
        "room_img",
        "owner",
        "is_personal",
    )

    list_filter = ("is_personal",)

    search_fields = ("room_name", "owner__username")

    autocomplete_fields = ("owner",)


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "authority_name",
        "authority_code",
    )

    search_fields = (
        "authority_name",
        "authority_code",
    )

@admin.register(RoomMember)
class RoomMemberAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "room",
        "user",
        "authority",
    )

    list_filter = (
        "authority",
    )

    search_fields = (
        "room__room_name",
        "user__username",
    )

    autocomplete_fields = (
        "room",
        "user",
        "authority",
    )

@admin.register(ToDoEvent)
class ToDo(admin.ModelAdmin):
    list_display = (
        "id",
        "event",
        "title",
        "checkTodo",
    )

    list_display_links = (
        "id",
    )