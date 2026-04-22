from django.contrib import admin

from .models import CustomUser
# Register your models here.
class CutomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'icon', 'username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_display_links = ('id', 'icon', 'username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ("username", "email")





# 管理サイトに models と admin を追加
admin.site.register(CustomUser, CutomUserAdmin)