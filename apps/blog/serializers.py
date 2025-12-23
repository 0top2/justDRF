from rest_framework import serializers
from apps.users.models import User
from .models import Post, Category


# 1. 简单的用户序列化器 (用于嵌套显示作者信息，防泄露密码)
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'bio']


# 2. 分类序列化器
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class AuthorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'bio']
# 3. 文章核心序列化器
class PostSerializer(serializers.ModelSerializer):
    # 嵌套显示：返回数据时，author 不再只是个 ID，而是一个包含头像用户名的字典
    author = AuthorDetailSerializer(read_only=True)

    # 动态字段：比如前端只想显示摘要
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'summary', 'body', 'author', 'category', 'status', 'created_at']
        read_only_fields = ['author', 'created_at']  # 作者由后端自动指定，不允许前端传

    def get_summary(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body

