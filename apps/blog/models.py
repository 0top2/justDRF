from django.db import models
from apps.users.models import User
# Create your models here.
class Tag(models.Model):
    """文章标签"""
    name = models.CharField("标签名称", max_length=20)
    def __str__(self):
        return self.name


class Category(models.Model):
    """文章分类"""
    name = models.CharField("分类名称", max_length=50)

    def __str__(self):
        return self.name


class Post(models.Model):
    """
    文章模型
    扩展性体现：
    1. 关联了 Category (多对一)
    2. 关联了 User (多对一)
    3. 包含了 created_at/updated_at 时间戳，方便做数据分析
    """
    title = models.CharField("标题", max_length=100)
    body = models.TextField("正文")

    # 这里的 settings.AUTH_USER_MODEL 就是指向 apps.users.User
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    # 状态字段 (草稿/发布)，工业级项目必备
    STATUS_CHOICES = (('draft', '草稿'), ('published', '发布'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
