"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# 引入你的 views
from apps.blog.views import PostViewSet, CategoryViewSet

# 自动注册路由
router = DefaultRouter()
router.register(r'articles', PostViewSet, basename='对文章的操作')
router.register(r'categories', CategoryViewSet, basename='对分类的操作')

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. 业务接口 /api/posts/
    path('api/', include(router.urls)),

    # 2. JWT 认证接口 (你要的 TokenObtain)
    path('api/token/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. 接口文档 (Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]


# {
#     "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc2NjY1MTkzNywiaWF0IjoxNzY2NTY1NTM3LCJqdGkiOiJmZGNjYTNhMzZiMmE0N2E1OTljNDEyNzQ5ODA4OTcwYyIsInVzZXJfaWQiOiIxIn0.DzdQQ6JlV44CiLzutde5OgXfBWpm1-vtGH1Et5HLZGM",
#     "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2NTY5MTM3LCJpYXQiOjE3NjY1NjU1MzcsImp0aSI6IjAxM2NkZDk3ZjBmMjQ3YWY5NjQ4NDQ4MzZmMmVhNjNmIiwidXNlcl9pZCI6IjEifQ.3AAvZnZbOUbuzFYisR5j5HnUkvWlnUVMaATGgLozdZ8"
# }