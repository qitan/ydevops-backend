#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   serialiser_cmdb.py
@time    :   2023/03/22 08:14
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
import json
from typing import List
from rest_framework import serializers

from django.db import transaction
from django.contrib.auth.models import User

from cmdb.models import Product, Project, Environment, KubernetesCluster, MicroApp, AppInfo, KubernetesDeploy


class ProductSerializers(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'


class ProjectSerializers(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('projectid', )

    @staticmethod
    def perform_extend_save(validated_data):
        _prefix = 'default'
        if validated_data.get('product', None):
            # 如果选择了产品，则取产品name为前缀
            _prefix = validated_data['product'].name
        if validated_data.get('parent', None):
            # 存在上一级项目，则取上一级项目name为前缀
            _prefix = validated_data['parent'].name
        if validated_data.get('name', None):
            validated_data['projectid'] = f"{_prefix}.{validated_data['name']}"

        return validated_data

    def create(self, validated_data):
        # 重写创建方法
        instance = Project.objects.create(
            **self.perform_extend_save(validated_data))
        return instance


class EnvironmentSerializers(serializers.ModelSerializer):

    class Meta:
        model = Environment
        fields = '__all__'


class KubernetesClusterDescSerializers(serializers.ModelSerializer):
    class Meta:
        model = KubernetesCluster
        fields = ('id', 'name', 'desc')


class KubernetesClusterListSerializers(serializers.ModelSerializer):
    config = serializers.SerializerMethodField()

    def get_config(self, instance):
        return json.loads(instance.config)

    class Meta:
        model = KubernetesCluster
        fields = '__all__'


class KubernetesClusterSerializers(serializers.ModelSerializer):
    class Meta:
        model = KubernetesCluster
        fields = '__all__'


class MicroAppListSerializers(serializers.ModelSerializer):
    project_info = serializers.SerializerMethodField()
    appinfo = serializers.SerializerMethodField()
    creator_info = serializers.SerializerMethodField()
    extra_team_info = serializers.SerializerMethodField()

    def get_project_info(self, instance):
        project = instance.project
        return {'project': {'id': project.id, 'alias': project.alias},
                'product': {'id': project.product.id, 'alias': project.product.alias}}

    def get_appinfo(self, instance):
        return [
            {'id': i.id, 'env_alias': i.environment.alias, 'env': {'name': i.environment.name, 'id': i.environment.id},
             'online': i.online} for i in instance.appinfo_set.all()]

    def get_creator_info(self, instance):
        try:
            return {'id': instance.creator.id, 'first_name': instance.creator.first_name,
                    'username': instance.creator.username}
        except BaseException as e:
            return {'id': '', 'first_name': '', 'username': ''}

    def get_extra_team_info(self, instance):
        data = {}
        for k, v in instance.extra_members.items():
            data[k] = [
                {'id': i.id, 'name': i.name,
                    'first_name': i.first_name, 'username': i.username}
                for i in User.objects.filter(id__in=v)
            ]
        return data

    class Meta:
        model = MicroApp
        fields = '__all__'


class MicroAppSerializers(serializers.ModelSerializer):
    class Meta:
        model = MicroApp
        fields = '__all__'
        read_only_fields = ('appid',)

    @staticmethod
    def perform_extend_save(validated_data):
        def default_value(fields: List):
            for field in fields:
                if validated_data.get(field):
                    if validated_data[field].get('key') != 'custom':
                        validated_data[field]['value'] = validated_data[field]['key']
            return validated_data

        validated_data = default_value(['dockerfile', 'target'])
        validated_data[
            'appid'] = f"{validated_data['project'].product.name}.{validated_data['project'].name}.{validated_data['name']}"
        return validated_data

    def create(self, validated_data):
        instance = MicroApp.objects.create(can_edit=[validated_data['creator'].id],
                                           **self.perform_extend_save(validated_data))
        return instance

    def update(self, instance, validated_data):
        return super().update(instance, self.perform_extend_save(validated_data))


class KubernetesDeploySerializers(serializers.ModelSerializer):
    kubernetes = KubernetesClusterDescSerializers()

    class Meta:
        model = KubernetesDeploy
        fields = '__all__'


class AppInfoListSerializers(serializers.ModelSerializer):
    app = MicroAppSerializers()
    kubernetes_info = serializers.SerializerMethodField()

    def get_kubernetes_info(self, instance):
        serializer = KubernetesDeploySerializers(
            data=KubernetesDeploy.objects.filter(appinfo=instance.id), many=True)
        serializer.is_valid()
        return serializer.data

    class Meta:
        model = AppInfo
        fields = '__all__'


class AppInfoSerializers(serializers.ModelSerializer):
    class Meta:
        model = AppInfo
        fields = '__all__'

    def perform_extend_save(self, validated_data, *args, **kwargs):
        if validated_data.get('app', None) and validated_data.get('environment', None):
            validated_data[
                'uniq_tag'] = f"{validated_data['app'].appid}.{validated_data['environment'].name.split('_')[-1].lower()}"

        if kwargs.get('instance', None):
            kubernetes = self.initial_data.get('kubernetes')
            _bulk = []
            for kid in kubernetes:
                _ks = KubernetesCluster.objects.get(id=kid)
                _bulk.append(KubernetesDeploy(
                    appinfo=kwargs['instance'], kubernetes=_ks))
            KubernetesDeploy.objects.bulk_create(_bulk, ignore_conflicts=True)
        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        instance = AppInfo.objects.create(
            **self.perform_extend_save(validated_data))
        if 'kubernetes' in self.initial_data:
            self.perform_extend_save(validated_data, **{'instance': instance})
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        KubernetesDeploy.objects.filter(appinfo=instance).delete()
        instance.__dict__.update(
            **self.perform_extend_save(validated_data, **{'instance': instance}))
        instance.save()
        return instance
