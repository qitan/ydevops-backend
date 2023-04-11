"""devops_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path, include

from cmdb import urls as cmdb_urls
from rest_framework.routers import DefaultRouter
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from ucenter.views import MenuViewSet, RoleViewSet, UserAuthTokenRefreshView, UserAuthTokenView, UserLogout, UserProfileViewSet, UserViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="DevOps运维平台",
        default_version='v1',
        description="DevOps运维平台 接口文档",
        terms_of_service="",
        contact=openapi.Contact(email="qqing_lai@hotmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()

# 用户模块
router.register('user/profile', UserProfileViewSet, basename='user-profile')
router.register('users', UserViewSet)
router.register('menus', MenuViewSet)
router.register('roles', RoleViewSet)


urlpatterns = [
    path('apidoc/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/user/login/', UserAuthTokenView.as_view(), name='user-login'),
    path('api/user/logout/', UserLogout.as_view(), name='user-logout'),
    path('api/user/refresh/', UserAuthTokenRefreshView.as_view(),
         name='token-refresh'),
    path('api/', include(cmdb_urls)),
]

# from devops_backend.settings import DEBUG
# if DEBUG:
#     # 兼容gunicorn启动
#     from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#     urlpatterns += staticfiles_urlpatterns()
