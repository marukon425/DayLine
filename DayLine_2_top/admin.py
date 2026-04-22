from django.contrib import admin

from .models import * 
# Register your models here.

# イベント
@admin.register(TermsOfUse)
class EventAdmin(admin.ModelAdmin):

    list_display = (
        "article_number",
        "article_name",
        "article_description"
    )

    list_display_links = (
        "article_number",
        "article_name",
        "article_description"
    )

