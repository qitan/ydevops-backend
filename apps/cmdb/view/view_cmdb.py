#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   view_cmdb.py
@time    :   2023/03/22 08:18
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
import json
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction

from cmdb.serializer.serialiser_cmdb import AppInfoListSerializers, AppInfoSerializers, KubernetesClusterListSerializers, KubernetesClusterSerializers, MicroAppListSerializers, MicroAppSerializers
from common.extends.decorators import cmdb_app_unique_check
from common.extends.viewsets import AutoModelViewSet, ops_response

from cmdb.models import Product, Project, Environment, KubernetesCluster, MicroApp, AppInfo, KubernetesDeploy
from cmdb.serializers import ProductSerializers, ProjectSerializers, EnvironmentSerializers

import logging

logger = logging.getLogger(__name__)


class ProductViewSet(AutoModelViewSet):
    """
    产品视图

    ### 产品权限
        {'*': ('product_all', '产品管理')},
        {'get': ('product_list', '查看产品')},
        {'post': ('product_create', '创建产品')},
        {'put': ('product_edit', '编辑产品')},
        {'patch': ('product_edit', '编辑产品')},
        {'delete': ('product_delete', '删除产品')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('product_all', '产品管理')},
        {'get': ('product_list', '查看产品')},
        {'post': ('product_create', '创建产品')},
        {'put': ('product_edit', '编辑产品')},
        {'patch': ('product_edit', '编辑产品')},
        {'delete': ('product_delete', '删除产品')}
    )
    queryset = Product.objects.all()
    serializer_class = ProductSerializers


class ProjectViewSet(AutoModelViewSet):
    """
    项目视图

    ### 项目权限
        {'*': ('project_all', '项目管理')},
        {'get': ('project_list', '查看项目')},
        {'post': ('project_create', '创建项目')},
        {'put': ('project_edit', '编辑项目')},
        {'patch': ('project_edit', '编辑项目')},
        {'delete': ('project_delete', '删除项目')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('project_all', '项目管理')},
        {'get': ('project_list', '查看项目')},
        {'post': ('project_create', '创建项目')},
        {'put': ('project_edit', '编辑项目')},
        {'patch': ('project_edit', '编辑项目')},
        {'delete': ('project_delete', '删除项目')}
    )
    queryset = Project.objects.all()
    serializer_class = ProjectSerializers


class EnvironmentViewSet(AutoModelViewSet):
    """
    区域视图

    ### 区域权限
        {'*': ('env_all', '区域环境管理')},
        {'get': ('env_list', '查看区域环境')},
        {'post': ('env_create', '创建区域环境')},
        {'put': ('env_edit', '编辑区域环境')},
        {'patch': ('env_edit', '编辑区域环境')},
        {'delete': ('env_delete', '删除区域环境')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('env_all', '区域环境管理')},
        {'get': ('env_list', '查看区域环境')},
        {'post': ('env_create', '创建区域环境')},
        {'put': ('env_edit', '编辑区域环境')},
        {'patch': ('env_edit', '编辑区域环境')},
        {'delete': ('env_delete', '删除区域环境')}
    )
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializers


class KubernetesClusterViewSet(AutoModelViewSet):
    """
    Kubernetes集群视图

    ### Kubernetes集群权限
        {'*': ('k8scluster_all', 'k8s集群管理')},
        {'get': ('k8scluster_list', '查看k8s集群')},
        {'post': ('k8scluster_create', '创建k8s集群')},
        {'put': ('k8scluster_edit', '编辑k8s集群')},
        {'patch': ('k8scluster_edit', '编辑k8s集群')},
        {'delete': ('k8scluster_delete', '删除k8s集群')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('k8scluster_all', 'k8s集群管理')},
        {'get': ('k8scluster_list', '查看k8s集群')},
        {'post': ('k8scluster_create', '创建k8s集群')},
        {'put': ('k8scluster_edit', '编辑k8s集群')},
        {'patch': ('k8scluster_edit', '编辑k8s集群')},
        {'delete': ('k8scluster_delete', '删除k8s集群')}
    )
    queryset = KubernetesCluster.objects.all()
    serializer_class = KubernetesClusterSerializers

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return KubernetesClusterListSerializers
        return KubernetesClusterSerializers


class MicroAppViewSet(AutoModelViewSet):
    """
    项目应用视图

    ### 项目应用权限
        {'*': ('microapp_all', '应用管理')},
        {'get': ('microapp_list', '查看应用')},
        {'post': ('microapp_create', '创建应用')},
        {'put': ('microapp_edit', '编辑应用')},
        {'patch': ('microapp_edit', '编辑应用')},
        {'delete': ('microapp_delete', '删除应用')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('microapp_all', '应用管理')},
        {'get': ('microapp_list', '查看应用')},
        {'post': ('microapp_create', '创建应用')},
        {'put': ('microapp_edit', '编辑应用')},
        {'patch': ('microapp_edit', '编辑应用')},
        {'delete': ('microapp_delete', '删除应用')}
    )
    queryset = MicroApp.objects.all()
    serializer_class = MicroAppSerializers

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return MicroAppListSerializers
        return MicroAppSerializers

    @cmdb_app_unique_check()
    def create(self, request, *args, **kwargs):
        """
        创建应用

        提交参数
        创建：{}
        """
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(methods=['POST'], url_path='related', detail=False)
    def app_related(self, request):
        """
        应用关联

        ### 传递参数:
            ids: 待关联应用id数组
            target: 目标应用id
        """
        try:
            target = request.data.get('target', None)
            ids = request.data.get('ids', None)
            if target:
                instance = self.queryset.get(id=target)
                ids.extend(instance.multiple_ids)
            self.queryset.filter(id__in=list(set(ids))).update(
                multiple_app=True, multiple_ids=list(set(ids)))
            return ops_response('应用关联成功.')
        except BaseException as e:
            logger.error('err', e)
            return ops_response({}, success=False, errorCode=50000, errorMessage='关联应用异常,请联系管理员!')

    @action(methods=['POST'], url_path='unrelated', detail=False)
    def app_unrelated(self, request):
        """
        取消应用关联

        ### 传递参数:
            id: 应用id
        """
        try:
            instance = self.queryset.filter(id=request.data.get('id'))
            # 获取关联应用ID列表
            ids = instance[0].multiple_ids
            ids.remove(instance[0].id)
            if len(ids) == 1:
                # 如果关联应用只剩下一个,则一起取消关联
                self.queryset.filter(id__in=instance[0].multiple_ids).update(
                    multiple_app=False, multiple_ids=[])
            else:
                # 更新其它应用的关联应用ID
                self.queryset.filter(id__in=ids).update(multiple_ids=ids)
                # 取消当前实例应用关联
                instance.update(multiple_app=False, multiple_ids=[])
            return ops_response('应用取消关联成功.')
        except BaseException as e:
            return ops_response({}, success=False, errorCode=50000, errorMessage=f'关联应用异常,请联系管理员! 原因：{e}')


class AppInfoViewSet(AutoModelViewSet):
    """
    项目应用服务

    * 服务对应着应用的不同环境，即应用每个环境创建一个对应的服务

    ### 项目应用服务权限
        {'*': ('microapp_all', '应用管理')},
        {'get': ('microapp_list', '查看应用')},
        {'post': ('microapp_create', '创建应用')},
        {'put': ('microapp_edit', '编辑应用')},
        {'patch': ('microapp_edit', '编辑应用')},
        {'delete': ('microapp_delete', '删除应用')}
    """
    perms_map = (
        {'*': ('admin', '管理员')},
        {'*': ('microapp_all', '应用管理')},
        {'get': ('microapp_list', '查看应用')},
        {'post': ('microapp_create', '创建应用')},
        {'put': ('microapp_edit', '编辑应用')},
        {'patch': ('microapp_edit', '编辑应用')},
        {'delete': ('microapp_delete', '删除应用')}
    )
    queryset = AppInfo.objects.all()
    serializer_class = AppInfoSerializers

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return AppInfoListSerializers
        return AppInfoSerializers

    def create(self, request, *args, **kwargs):
        request.data['uniq_tag'] = 'default'
        return super().create(request, *args, **kwargs)
