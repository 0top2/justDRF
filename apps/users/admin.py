from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 使用 Django 自带的 UserAdmin 来管理你的自定义用户
admin.site.register(User, UserAdmin)