from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Category
from .serializers import PostSerializer, CategorySerializer


# 自定义权限：只有作者能改，别人只能看 (对象级权限)
class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return obj.author == request.user


class PostViewSet(viewsets.ModelViewSet):
    """
    文章接口
    支持：增删改查、分页、搜索、筛选、排序
    """
    # 1. 优化查询：使用 select_related 解决 N+1 问题 (Author是外键)
    # queryset = Post.objects.select_related('author', 'category').filter(status='published')
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    # 2. 权限控制
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    #
    # # 3. 搜索与筛选 (工业级标配)
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filterset_fields = ['category', 'author']  # 支持 ?category=1
    # search_fields = ['title', 'body']  # 支持 ?search=Python
    # ordering_fields = ['created_at', 'id']  # 支持 ?ordering=-created_at

    # 4. 重写 perform_create：自动把当前登录用户设为作者
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # 分类随便谁都能看，但只有管理员能改
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]