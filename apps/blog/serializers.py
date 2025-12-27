from rest_framework import serializers
from apps.users.models import User
from .models import Post, Category, Tag


# 1. 简单的用户序列化器 (用于嵌套显示作者信息，防泄露密码)
class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'bio']
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

# 2. 分类序列化器
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# 3. 文章核心序列化器
class PostSerializer(serializers.ModelSerializer):
    # 嵌套显示：返回数据时，author 不再只是个 ID，而是一个包含头像用户名的字典
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)  #只从数据库里读数据
    tags_ids = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True,
                                                  write_only=True, required=False,
                                                  source='tags')
    # 动态字段：比如前端只想显示摘要
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'summary', 'body', 'author', 'tags','tags_ids', 'category', 'status', 'created_at','views']
        read_only_fields = ['author', 'created_at','views']  # 作者由后端自动指定，不允许前端传

    def get_summary(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body

