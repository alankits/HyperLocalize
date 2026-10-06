"""UC8 user administration through Django's admin site (Administrators only)."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ProjectMembership, User


@admin.register(User)
class HLUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("HyperLocalize", {"fields": ("is_administrator",)}),)
    list_display = ("username", "email", "is_administrator", "is_active", "last_login")


@admin.register(ProjectMembership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "role")
    list_filter = ("role",)
