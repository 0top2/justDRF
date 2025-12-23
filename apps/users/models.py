from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    """
        自定义用户模型
        扩展性体现：
        1. 继承 AbstractUser，保留了 django 自带的所有好功能 (密码加密、组权限)
        2. 预留了 bio (简介) 和 avatar (头像)
        3. 未来如果要加 'phone_number'，直接在这里加字段并 migrate 即可，无需重构代码
        """
    bio = models.TextField("个人简介", blank=True, null=True)
    # 实际项目中通常会用 ImageField，这里用 URL 简化演示
    avatar = models.URLField("头像", blank=True, null=True)
    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username