import json

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
    def retrieve(self, request, pk=None,*args,**kwargs):
        cache_key = f"post:detail:{pk}"
        view_key = f"post:{pk}:view_count"
        user = request.user

    #先处理浏览量 ----------------------------------------------------
        if not redis.exists(view_key):
            # 极端情况：Redis 丢数据了，这里才需要被迫查库（只会发生 1 次）
            # 为了代码简洁，这里可以直接给个初始值，或者回源查一次
            try:
                # 这里的查询是为了容错，虽有性能损耗但概率极低
                view_data = Post.objects.values('views').get(pk=pk)
                db_views = view_data['views']
                redis.set(view_key, db_views + 1, ex=86400)
                current_views = db_views + 1
            except Post.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            current_views = redis.incr(view_key)
    #-------------------------------------------------------------
    #然后处理内容缓存的问题------------------------------------------
        cache_data = redis.get(cache_key)
        #只在redis里存储公共部分
        if cache_data:
            print("命中缓存")
            data = json.loads(cache_data)
            if user.is_authenticated:
                is_like = redis.sismember(f"post:{pk}:like_member", user.id)
            else:
                is_like = False
            data["is_like"] = is_like
        else:
            instance = self.get_object()
            print("没有命中缓存,回源查询")
            serializer = self.get_serializer(instance)
            data = serializer.data
            if "is_like" in data:
                data.pop("is_like")
            redis.set(cache_key, json.dumps(data), ex=86400)
            if user.is_authenticated:
                data["is_like"] = instance.likes.filter(id=user.id).exists()
            else:
                data["is_like"] = False

        # #不管redis有没有,都要去处理的私密数据
        # if request.user.is_authenticated:
        #     data["is_like"] = instance.likes.filter(id=request.user.id).exists()
        # else:
        #     is_like = False
        data["views"] = current_views
        if current_views % 10 == 0:
            # 这里为了不影响响应速度，可以用 celery 异步，或者用简单的 update 语句
            # 使用 update 语句极快，不会加载对象，也不会触发信号
            Post.objects.filter(pk=pk).update(views=current_views)
            print(f"💾 [MySQL] 浏览量已同步: {current_views}")
        return Response(data, status=status.HTTP_200_OK)

    def peform_update(self, serializer):
        instance = serializer.save()
        cache_key = f"post:detail:{instance.pk}"
        redis.delete(cache_key)
    def perform_destroy(self, instance):
        pk = instance.id
        instance.delete()
        cache_key = f"post:detail:{pk}"
        redis.delete(cache_key)
        redis.delete(f"post:{pk}:view_count")

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.select_related('author','category').prefetch_related('tags').all()
        if user.is_authenticated:
            return queryset.filter(Q(author=user)|Q(status='published'))
        return queryset.filter(status='published')
    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = self.request.user
        like_key = f"post:{pk}:like_member"  #点赞作者名单
    #先看有没有这个键位,如果没有就读一遍数据库,存放到redis
        if not redis.exists(like_key):
            user_ids = post.likes.values_list('id', flat=True)
            if user_ids:
                redis.sadd(like_key, *user_ids)
            redis.expire(like_key, 86400)
    #再去判断点赞/取消点赞逻辑
        if redis.sismember(like_key, user.id):
            post.likes.remove(request.user)
            redis.srem(like_key, user.id)
            action = '-'
            message="取消点赞"
        else:
            post.likes.add(request.user)
            redis.sadd(like_key, user.id)
            action = '+'
            message = '点赞成功'

        final_count = redis.scard(like_key)
        return Response({'message': message,
                         'like_count': final_count
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
        serializer.save(author=self.request.user)
        return Response({
            "message":"评论成功"
        })