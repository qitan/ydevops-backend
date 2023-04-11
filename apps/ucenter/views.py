#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   views.py
@time    :   2023/03/26 14:36
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
import hashlib
import django_filters
import shortuuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import pagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.db.models import Q
from django.core.cache import cache
from django.contrib.auth import logout
from django.contrib.auth.models import update_last_login

from ucenter.models import UserProfile, Menu, Role, Permission, Organization
from ucenter.serializers import MenuSerializers, MenuListSerializers, PermissionSerializers, PermissionListSerializers, RoleSerializers, RoleListSerializers, OrganizationSerializers, UserProfileListSerializers, UserProfileDetailSerializers, UserProfileMenuSerializers, UserProfileSerializers

from common.extends.viewsets import AutoModelViewSet, AutoModelParentViewSet, ops_response
from common.extends.jwt_auth import TokenObtainPairSerializer, TokenRefreshSerializer, CustomInvalidToken
from config import USER_AUTH_BACKEND

import logging

logger = logging.getLogger(__name__)


USER_SYNC_KEY = {
    'feishu': 'celery_job:feishu_user_sync',  # 同步飞书组织架构任务key
    'ldap': 'celery_job:ldap_user_sync',  # LDAP用户同步任务KEY
}


class MenuViewSet(AutoModelParentViewSet):
    """
    菜单视图

    ### 菜单权限
        {'*': ('menu_all', '菜单管理')},
        {'get': ('menu_list', '查看菜单')},
        {'post': ('menu_create', '创建菜单')},
        {'put': ('menu_edit', '编辑菜单')},
        {'patch': ('menu_edit', '编辑菜单')},
        {'delete': ('menu_delete', '删除菜单')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('menu_all', '菜单管理')},
        {'get': ('menu_list', '查看菜单')},
        {'post': ('menu_create', '创建菜单')},
        {'put': ('menu_edit', '编辑菜单')},
        {'patch': ('menu_edit', '编辑菜单')},
        {'delete': ('menu_delete', '删除菜单')}
    )
    queryset = Menu.objects.all()
    serializer_class = MenuSerializers
    serializer_list_class = MenuListSerializers
    serializer_retrieve_class = MenuListSerializers
    exclude_columns = ['id', 'parent', 'created_time', 'update_time',
                       'is_frame', 'hidden', 'spread', 'affix']
    extra_columns = [{'id': 'parent', 'dataIndex': 'parent',
                      'title': '上级', 'type': 'related', 'required': False}]
    column_width = {'name': 140}


class PermissionViewSet(AutoModelParentViewSet):
    """
    权限视图

    ### 查看权限列表的权限
        {'*': ('perm_all', '权限管理')},
        {'get': ('perm_list', '查看权限')},
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('perm_all', '权限管理')},
        {'get': ('perm_list', '查看权限')}
    )
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializers
    serializer_list_class = PermissionListSerializers
    serializer_retrieve_class = PermissionListSerializers


class RoleViewSet(AutoModelViewSet):
    """
    角色视图

    ### 角色管理权限
        {'*': ('role_all', '角色管理')},
        {'get': ('role_list', '查看角色')},
        {'post': ('role_create', '创建角色')},
        {'put': ('role_edit', '编辑角色')},
        {'patch': ('role_edit', '编辑角色')},
        {'delete': ('role_delete', '删除角色')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('role_all', '角色管理')},
        {'get': ('role_list', '查看角色')},
        {'post': ('role_create', '创建角色')},
        {'put': ('role_edit', '编辑角色')},
        {'patch': ('role_edit', '编辑角色')},
        {'delete': ('role_delete', '删除角色')}
    )
    queryset = Role.objects.exclude(name='thirdparty')
    serializer_class = RoleSerializers
    serializer_list_class = RoleListSerializers
    serializer_retrieve_class = RoleListSerializers

    def perform_destroy(self, instance):
        if instance.name != '默认角色':
            instance.delete()


class OrganizationViewSet(AutoModelParentViewSet):
    """
    组织架构视图

    ### 组织架构权限
        {'*': ('org_all', '组织架构管理')},
        {'get': ('org_list', '查看组织架构')},
        {'post': ('org_create', '创建组织架构')},
        {'put': ('org_edit', '编辑组织架构')},
        {'patch': ('org_edit', '编辑组织架构')},
        {'delete': ('org_delete', '删除组织架构')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('org_all', '组织架构管理')},
        {'get': ('org_list', '查看组织架构')},
        {'post': ('org_create', '创建组织架构')},
        {'put': ('org_edit', '编辑组织架构')},
        {'patch': ('org_edit', '编辑组织架构')},
        {'delete': ('org_delete', '删除组织架构')}
    )
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializers
    serializer_organization_users_class = UserProfileListSerializers

    def get_queryset(self):
        if self.action == 'organization_users':
            qs = self.queryset.get(pk=self.request.query_params['org_id'])
            return self.get_org_users(qs).distinct()
        return super().get_queryset()

    def get_org_users(self, org):
        qs = org.org_user.all()
        for i in org.children.all():
            qs |= self.get_org_users(i)
            # qs = qs.distinct()
        return qs

    @action(methods=['GET'], url_path='users', detail=False)
    def organization_users(self, request, *args, **kwargs):
        return super().list(request, pk=None, *args, **kwargs)


class UserViewSet(AutoModelViewSet):
    """
    用户管理视图

    ### 用户管理权限
        {'*': ('user_all', '用户管理')},
        {'get': ('user_list', '查看用户')},
        {'post': ('user_create', '创建用户')},
        {'put': ('user_edit', '编辑用户')},
        {'patch': ('user_edit', '编辑用户')},
        {'delete': ('user_delete', '删除用户')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('user_all', '用户管理')},
        {'get': ('user_list', '查看用户')},
        {'post': ('user_create', '创建用户')},
        {'put': ('user_edit', '编辑用户')},
        {'patch': ('user_edit', '编辑用户')},
        {'delete': ('user_delete', '删除用户')}
    )
    queryset = UserProfile.objects.exclude(
        Q(username='thirdparty'))
    serializer_class = UserProfileSerializers
    serializer_list_class = UserProfileListSerializers
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = {
        'position': ['exact'],
        'title': ['exact'],
        'id': ['in', 'exact'],
    }
    search_fields = ('position', 'mobile', 'title',
                     'username', 'first_name', 'email')
    include_columns = ['username', 'first_name',
                       'position', 'email', 'is_superuser', 'is_active']
    extra_columns = [{'id': 'department', 'dataIndex': 'department',
                      'title': '部门', 'type': 'm2m', 'required': True}]

    def get_serializer_class(self):
        if self.action == 'detail' or self.action == 'retrieve':
            return UserProfileDetailSerializers
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        if self.queryset.filter(username=request.data['username']):
            return ops_response({}, success=False, errorCode=40300, errorMessage='%s 账号已存在!' % request.data['username'])
        password = shortuuid.ShortUUID().random(length=8)
        # md5加密password
        pwd = hashlib.md5()
        pwd.update(password.encode(encoding='utf-8'))
        request.data['password'] = pwd.hexdigest()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        data['password'] = password
        data['code'] = 20000
        return ops_response(data)

    def perform_destroy(self, instance):
        """
        用户启用禁用
        """
        # 禁用用户
        instance.is_active = not instance.is_active
        instance.save()

    @action(methods=['POST'], url_path='password/reset', detail=False)
    def password_reset(self, request):
        """
        重置用户密码

        ### 重置用户密码
        """
        data = self.request.data
        user = self.queryset.get(pk=data['uid'])
        if user.is_superuser:
            return ops_response({}, success=False, errorCode=40300, errorMessage='禁止修改管理员密码！')
        # md5加密password
        pwd = hashlib.md5()
        pwd.update(data['password'].encode(encoding='utf-8'))
        user.set_password(pwd.hexdigest())
        user.save()
        return ops_response('密码已更新.')

    @action(methods=['GET'], url_path='detail', detail=False)
    def detail_info(self, request, pk=None, *args, **kwargs):
        """
        用户详细列表

        ### 获取用户详细信息，用户管理模块
        """
        return super().list(request, pk, *args, **kwargs)

    @action(methods=['POST'], url_path='sync', detail=False)
    def user_sync(self, request):
        """
        用户同步

        ### 传递参数:
            sync: 1
        """
        sync = request.data.get('sync', 0)
        is_job_exist = cache.get(USER_SYNC_KEY[USER_AUTH_BACKEND])
        if is_job_exist:
            return ops_response({}, success=False, errorCode=40300, errorMessage='已经有组织架构同步任务在运行中... 请稍后刷新页面查看')

        if sync:
            # 同步任务
            taskid = None
            # 限制只能有一个同步任务在跑
            cache.set(USER_SYNC_KEY[USER_AUTH_BACKEND], taskid, timeout=300)
        return ops_response('正在同步组织架构信息...')


class UserAuthTokenView(TokenObtainPairView):
    """
    用户登录视图
    """
    perms_map = ()
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        data = None
        try:
            if not serializer.is_valid():
                logger.exception(f'用户登录异常{serializer.errors}')
            else:
                data = serializer.validated_data
                # 用户登录成功,绑定默认角色并更新最后登录时间
                user = UserProfile.objects.get(
                    username=request.data['username'])
                try:
                    role = Role.objects.get(name='默认角色')
                    user.roles.add(*[role.id])
                except BaseException as e:
                    logger.exception(f"绑定用户角色失败, 原因: {e}")
                # update_last_login(None, user)
        except BaseException as e:
            logger.exception(f"用户登录异常, 原因: {e}")

            raise CustomInvalidToken(e.args[0], code=40100)

        return ops_response(data)


class UserAuthTokenRefreshView(TokenRefreshView):
    """
    用户token刷新视图
    """
    perms_map = ()
    serializer_class = TokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            data['username'] = request.user.username
        except TokenError as e:
            logger.error(f"刷新用户token异常, 原因: {e}")
            raise CustomInvalidToken(e.args[0], code=40101)
        return ops_response(data)


class UserLogout(APIView):
    """
    用户注销视图
    """
    perms_map = ()

    def get(self, request, format=None):
        # token.blacklist()
        # # simply delete the token to force a login
        # request.user.auth_token.delete()
        logout(request)
        return ops_response('用户已退出')

    def post(self, request, format=None):
        # token.blacklist()
        # # simply delete the token to force a login
        # request.user.auth_token.delete()
        logout(request)
        return ops_response('用户已退出')


class UserProfileViewSet(AutoModelViewSet):
    """
    用户信息视图

    ### 用户信息管理权限
        {'*': ('userinfo_all', '用户信息管理')},
        {'get': ('userinfo_list', '查看用户信息')},
        {'put': ('userinfo_edit', '编辑用户信息')},
        {'patch': ('userinfo_edit', '编辑用户信息')},
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('userinfo_all', '用户信息管理')},
        {'get': ('userinfo_list', '查看用户信息')},
        {'put': ('userinfo_edit', '编辑用户信息')},
        {'patch': ('userinfo_edit', '编辑用户信息')},
    )
    queryset = UserProfile.objects.exclude(
        username='thirdparty').order_by('id')
    # authentication_classes = [JWTAuthentication, ]
    serializer_class = UserProfileDetailSerializers
    serializer_menus_class = UserProfileMenuSerializers
    # permission_classes = [RbacPermission, ]
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend, OrderingFilter)
    filter_fields = ('user', 'type', 'action', 'action_ip', 'operator')
    search_fields = ('user', 'type', 'action', 'action_ip', 'content')

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return UserProfileSerializers
        return UserProfileDetailSerializers

    def update(self, request, *args, **kwargs):
        instance = self.queryset.get(username=request.user)
        instance.__dict__.update(**request.data)
        instance.save()
        serializer = self.get_serializer(instance)
        return ops_response(serializer.data)

    def menu_sort(self, menus):
        """
        菜单排序
        sort值越小越靠前
        :param menus:
        :return:
        """
        for menu in menus:
            try:
                if menu['children']:
                    self.menu_sort(menu['children'])
            except KeyError:
                pass
        try:
            menus.sort(key=lambda k: (k.get('sort')))
        except:
            pass
        return menus

    @action(methods=['GET'], url_path='info', detail=False)
    def info(self, request):
        """
        获取用户信息
        :param request:
        :return:
        """
        serializer = self.get_serializer(request.user)
        data = serializer.data
        data.pop('password', None)
        data.pop('routers', None)
        data['roles'] = ['admin'] if request.user.is_superuser else [
            i['name'] for i in data['user_roles']]
        return ops_response(data)

    @action(methods=['GET'], url_path='menus', detail=False)
    def menus(self, request):
        """
        获取用户菜单
        :param request:
        :return:
        """
        serializer = self.get_serializer(request.user)
        data = serializer.data
        routers = data['routers']
        routers = self.menu_sort(routers)
        return ops_response(routers)

    @action(methods=['POST'], url_path='system/dict/invalid-hash', detail=False)
    def expired_hash(self, request):
        # TODO: 临时，将来移到system模块
        return ops_response([])
