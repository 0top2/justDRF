from django.db.models import Q
from utils.redis_pool import redis

# Create your views here.
from rest_framework import viewsets, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Post, Category, Comment
from .serializers import PostSerializer, CategorySerializer, CommentSerializer, PostDetailSerializer


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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['created_at', 'views']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    # 2. 权限控制
    # permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    #
    # # 3. 搜索与筛选 (工业级标配)
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filterset_fields = ['category', 'author']  # 支持 ?category=1
    # search_fields = ['title', 'body']  # 支持 ?search=Python
    # ordering_fields = ['created_at', 'id']  # 支持 ?ordering=-created_at


    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer
    # 4. 重写 perform_create：自动把当前登录用户设为作者
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    def retrieve(self, request, pk=None):
        instance = self.get_object()
        view_key = f"post:{pk}:view_count"
        if not redis.exists(view_key):
            redis.set(view_key, instance.views+1 , ex=86400)
            instance.views = redis.get(view_key)
        else:
            new_view = redis.incr(view_key)
            instance.views  = new_view
        instance.save(update_fields=['views'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Post.objects.filter(Q(author=user)|Q(status='published'))
        return Post.objects.filter(status='published')
    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = self.request.user
        count_key = f"post:{pk}:like_count"
        if post.likes.filter(id=user.id).exists():
            post.likes.remove(request.user)
            action = '-'
            message="取消点赞"
        else:
            post.likes.add(request.user)
            action = '+'
            message = '点赞成功'
        if not redis.exists(count_key):
            current_count = post.likes.count()
            redis.set(count_key, current_count)
        else:
            if action == '+':
                redis.incr(count_key)
            elif action == '-':
                redis.decr(count_key)
        final_count = redis.get(count_key)
        return Response({'message': message,
                         'like_count': int(final_count)
                         }
                        )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # 分类随便谁都能看，但只有管理员能改
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        print("\n\n=============== 我运行到了这里！===============\n\n")
        serializer.save(author=self.request.user)
        return Response({
            "message":"评论成功"
        })