from django.contrib import admin
from .models import Post, Category,Tag

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # 在列表页显示这些字段
    list_display = ('title', 'author', 'category', 'status', 'created_at')
    # 允许点击这两个字段进入编辑
    list_display_links = ('title',)
    # 侧边栏筛选器
    list_filter = ('status', 'category')
    # 搜索框
    search_fields = ('title', 'body')

@admin.register(Tag)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')