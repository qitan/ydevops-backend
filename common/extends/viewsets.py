#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   viewsets.py
@time    :   2023/03/26 14:42
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
import inspect
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework import pagination
from rest_framework.settings import api_settings
from rest_framework.filters import OrderingFilter
from django.db.models.query import QuerySet
from django.db.models import ProtectedError, fields
from django.core.cache import cache
import pytz
import logging

logger = logging.getLogger(__name__)


def ops_response(data, code=20000, message=None, status=status.HTTP_200_OK):
    """
    返回自定义
    data列表数据格式：{
 list: [
 ],
 total?: number,
 next: string,
 previous: string
}
    """
    return Response({'data': data, 'code': code, 'message': message}, status=status)


class AutoModelViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """

    permission_classes = [IsAuthenticated]
    permission_classes_by_action = {}
    filter_backends = (OrderingFilter, )
    column_width = {}

    def __init__(self, *args, **kwargs):
        if not hasattr(self, 'queryset'):
            raise AttributeError('必须定义 类属性 queryset')

        if not hasattr(self, 'serializer_class'):
            raise AttributeError('必须定义 类属性 serializer_class')

        super().__init__(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        """
        重写 get_serializer 类，用来支持自动获取不同的 serializer_class
        例子：  list 方法， 设置一个serializer_list_class， 则调用get_serializer的时候， 优先获取
        命名格式 serializer_{call_func_name}_class
        :param args:
        :param kwargs:
        :return:
        """
        call_func_name = inspect.stack()[1][3]
        serializer_class = getattr(
            self, f'serializer_{call_func_name}_class', None)
        if not serializer_class:
            serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_object(self):
        return super(AutoModelViewSet, self).get_object()

    def get_permissions(self):
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]

    def get_permission_from_role(self, request):
        try:
            perms = request.user.roles.values(
                'permissions__method',
            ).distinct()
            return [p['permissions__method'] for p in perms]
        except (AttributeError, TypeError):
            return []

    def extend_filter(self, queryset):
        return queryset

    def get_queryset(self):
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )
        queryset = self.extend_filter(self.queryset)
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        try:
            request.data['name'] = request.data['name'].strip(
                ' ').replace(' ', '-')
        except BaseException as e:
            logger.debug('exception ', str(e))
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ops_response({}, code=40000, message=str(serializer.errors), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            self.perform_create(serializer)
        except BaseException as e:
            return ops_response({}, code=50000, message=str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return ops_response(serializer.data)

    def list(self, request, pk=None, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page_size = request.query_params.get('page_size', None)
        get_all = request.query_params.get('get_all', None)
        if not page_size:
            page_size = api_settings.PAGE_SIZE
        pagination.PageNumberPagination.page_size = page_size
        page = self.paginate_queryset(queryset)
        if not get_all and page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return ops_response({'list': serializer.data, 'total': queryset.count()})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        try:
            request.data['name'] = request.data['name'].strip(
                ' ').replace(' ', '-')
        except BaseException as e:
            logger.warning(f'不包含name字段: {str(e)}')
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return ops_response({}, code=40000, message=str(serializer.errors))
        try:
            self.perform_update(serializer)
        except BaseException as e:
            return ops_response({}, code=50000, message=str(e))

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return ops_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ops_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            # 存在关联数据，不可删除
            return ops_response({}, code=40300, message='存在关联数据，禁止删除！')
        except BaseException as e:
            logger.exception(f'删除数据发生错误 {e}, {e.__class__}')
            return ops_response({}, code=50000, message=f'删除异常： {str(e)}')
        return ops_response('删除成功')

    @action(methods=['GET'], url_path='columns', detail=False)
    def model_columns(self, request):
        """
        获取字段
        """
        columns = [i for i in self.queryset.model._meta.fields if i.name not in [
            'created_time', 'update_time']]
        data = [{'id': i.name, 'title': i.verbose_name, 'dataIndex': i.name, 'type': self.queryset.model._meta.get_field(i.name).get_internal_type(), 'width': self.column_width.get(i.name, None),  'required': not i.null, 'default': None if i.default == fields.NOT_PROVIDED else i.default}
                for i in columns]
        if hasattr(self, 'include_columns'):
            data = [i for i in data if i['id'] in self.include_columns]
        if hasattr(self, 'exclude_columns'):
            data = [i for i in data if i['id'] not in self.exclude_columns]
        if hasattr(self, 'extra_columns'):
            data.extend(self.extra_columns)
        return ops_response(data)


class AutoModelParentViewSet(AutoModelViewSet):

    def get_queryset(self):
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )
        queryset = self.extend_filter(self.queryset)
        if self.action == 'list':
            if not self.request.query_params.get('search'):
                queryset = queryset.filter(parent__isnull=True)
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        return queryset.distinct()
