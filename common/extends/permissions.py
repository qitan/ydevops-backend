#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   permissions.py
@time    :   2023/03/26 15:27
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
from rest_framework.permissions import BasePermission

from config import PLATFORM_CONFIG

import logging

logger = logging.getLogger(__name__)


class RbacPermission(BasePermission):
    """
    自定义权限
    """

    @classmethod
    def check_is_admin(cls, request):
        return request.user.is_authenticated and request.user.roles.filter(name='管理员').count() > 0

    @classmethod
    def get_permission_from_role(cls, request):
        try:
            perms = request.user.roles.values(
                'permissions__method',
            ).distinct()
            return [p['permissions__method'] for p in perms]
        except AttributeError:
            return []

    def _has_permission(self, request, view):
        """
        权限获取方式
            从 perms_map 中获取， 通过 request.method, http 请求方法来获取对应权限点
            1. 默认格式
                perms_map = (
                    {'*': ('admin', '管理员')},
                    {'*': ('k8s_all', 'k8s管理')},
                    {'get': ('k8s_list', '查看k8s')},
                    {'post': ('k8s_create', '创建k8s')},
                    {'put': ('k8s_edit', '编辑k8s')},
                    {'delete': ('k8s_delete', '删除k8s')}
                )
            2. 自定义方法格式
                perms_map = (
                    {'get_test_data': ('get_test_data', '获取测试数据')},
                )
                此时 格式为  {http请求方法}_{ViewSet自定义action}

        :param request: rest_framework request 对象
        :param view: rest_framework view 对象
        :return:
        """
        _method = request._request.method.lower()
        url_whitelist = PLATFORM_CONFIG['whitelist'] if PLATFORM_CONFIG.get(
            'whitelist', None) else []
        path_info = request.path_info
        for item in url_whitelist:
            url = item['url']
            if url in path_info:
                logger.debug(f'请求地址 {path_info} 命中白名单 {url}， 放行')
                return True

        is_superuser = request.user.is_superuser
        # 超级管理员 或者 白名单模式 直接放行
        if is_superuser:
            logger.debug(
                f'用户 {request.user} 是超级管理员， 放行 is_superuser = {is_superuser}')
            return True

        is_admin = RbacPermission.check_is_admin(request)
        perms = self.get_permission_from_role(request)
        # 不是管理员 且 权限列表为空的情况下， 直接拒绝
        if not is_admin and not perms:
            logger.debug(f'用户 {request.user} 不是管理员 且 权限列表为空， 直接拒绝')
            return False

        perms_map = view.perms_map
        # 未配置权限映射的视图一律禁止访问
        if not hasattr(view, 'perms_map'):
            logger.debug(f'未配置权限映射的视图一律禁止访问 {view}')
            return False

        # _custom_method = None
        # default_funcs = ['create', 'list', 'retrieve', 'update', 'destroy']
        action = view.action
        _custom_method = f'{_method}_{action}'
        for i in perms_map:
            logger.debug(f'perms_map item ===  {i}')
            for method, alias in i.items():
                # 如果是管理员， 判断当前perms_map是否带有 {'*': ('admin', '管理员')} 标记，如果有， 则当前 ViewSet 所有方法全放行
                if is_admin and (method == '*' and alias[0] == 'admin'):
                    logger.debug('管理员判断通过， 放行')
                    return True
                # 如果带有某个模块的管理权限， 则当前模块所有方法都放行
                if method == '*' and alias[0] in perms:
                    logger.debug('模块管理权限 判断通过， 放行')
                    return True

                # 判断自定义action的情况
                # {'get_test_data': ('get_test_data', '获取测试数据')},
                # {'*_test_data': ('get_test_data', '获取测试数据')},
                if _custom_method and alias[0] in perms and (_custom_method == method or method == f'*_{action}'):
                    logger.debug('自定义action权限 判断通过， 放行')
                    return True

                # 判断是否拥有ViewSet 某个方法的权限， 有则放行
                # {'get': ('workflow_list', '查看工单')},
                if _method == method and alias[0] in perms:
                    logger.debug(f'{method}方法权限 判断通过， 放行')
                    return True
        logger.debug(f'{path_info} 没有符合条件的， 则默认禁止访问')
        return False

    def has_permission(self, request, view):
        res = self._has_permission(request, view)
        # 记录权限异常的操作
        if not res:
            pass
        return res


class AdminPermission(BasePermission):

    def has_permission(self, request, view):
        if RbacPermission.check_is_admin(request):
            return True
        return False


class ObjPermission(BasePermission):
    """
    密码管理对象级权限控制
    """

    def has_object_permission(self, request, view, obj):
        perms = RbacPermission.get_permission_from_role(request)
        if 'admin' in perms:
            return True
        elif request.user.id == obj.uid_id:
            return True
