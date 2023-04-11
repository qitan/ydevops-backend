#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@author  :   Charles Lai
@file    :   model_cmdb.py
@time    :   2023/03/22 07:42
@contact :   qqing_lai@hotmail.com
'''

# here put the import lib
from django.db import models
# from django.contrib.auth.models import User

from ucenter.models import UserProfile as User
from .model_assets import Idc, Region
from common.extends.models import TimeAbstract, CommonParent


class DevLanguage(TimeAbstract):
    name = models.CharField(max_length=100, unique=True, verbose_name='开发语言')
    alias = models.CharField(max_length=128, default='', verbose_name='别名')
    base_image = models.JSONField(default=dict, verbose_name='基础镜像',
                                  help_text='{"project": "", "project_id": "", "image": "", "tag": ""}')
    build = models.JSONField(default=dict, verbose_name='构建命令')
    dockerfile = models.TextField(
        null=True, blank=True, default='', verbose_name='Dockerfile模板')
    pipeline = models.TextField(
        null=True, blank=True, default='', verbose_name='流水线模板')
    desc = models.TextField(verbose_name='描述', null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    class ExtMeta:
        related = True
        dashboard = True

    class Meta:
        verbose_name = '开发语言'
        verbose_name_plural = verbose_name + '管理'


class Environment(TimeAbstract):
    """环境"""
    name = models.CharField(max_length=100, unique=True, verbose_name='环境')
    alias = models.CharField(max_length=128, default='', verbose_name='环境别名')
    ticket_on = models.SmallIntegerField(default=0, choices=((0, '不启用'), (1, '启用')), verbose_name='启用工单',
                                         help_text="是否启用工单\n(0, '不启用'), (1, '启用'), 默认: 0")
    merge_on = models.SmallIntegerField(default=0, choices=((0, '不启用'), (1, '启用')), verbose_name='分支合并',
                                        help_text="是否要求分支合并\n(0, '不启用'), (1, '启用'), 默认: 0")
    template = models.JSONField(
        default=dict, verbose_name='应用KubernetesDeployment配置')
    allow_ci_branch = models.JSONField(default=list, verbose_name='允许构建的分支',
                                       help_text="存储数组格式，具体的分支名; 默认['*'], 表示允许所有分支.")
    allow_cd_branch = models.JSONField(default=list, verbose_name='允许发布的分支',
                                       help_text="存储数组格式，具体的分支名; 默认['*'], 表示允许所有分支.")
    extra = models.JSONField(
        default=dict, verbose_name='额外参数', help_text='更多参数')
    desc = models.TextField(null=True, blank=True, verbose_name='环境描述')

    def __str__(self):
        return self.name

    class ExtMeta:
        related = True
        dashboard = True

    class Meta:
        verbose_name = '环境'
        verbose_name_plural = verbose_name + '管理'


class Product(TimeAbstract, CommonParent):
    name = models.CharField(max_length=100, unique=True, verbose_name='产品')
    alias = models.CharField(max_length=128, default='', verbose_name='产品别名')
    region = models.ForeignKey(
        Region, blank=True, null=True, on_delete=models.PROTECT, verbose_name='区域')
    desc = models.TextField(verbose_name='详情描述', null=True, blank=True)
    prefix = models.CharField(
        max_length=100, null=True, blank=True, verbose_name='前缀')
    creator = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, verbose_name='产品创建人',
                                help_text='前端不需要传递')
    managers = models.JSONField(default=dict, verbose_name='负责人',
                                help_text='存储格式 对象: {"product": userid, "develop": userid}；product: 产品负责人, develop: 技术负责人；值为int类型，存储用户ID.')

    def __str__(self):
        return self.name

    class ExtMeta:
        related = True
        dashboard = True
        icon = 'asset4'

    class Meta:
        verbose_name = '产品'
        verbose_name_plural = verbose_name + '管理'


def get_default_extra_members():
    return {
        'dev': {'name': '开发人员', 'members': []},
        'op': {'name': '运维人员', 'members': []},
        'test': {'name': '测试人员', 'members': []},
        'product': {'name': '产品人员', 'members': []}
    }


class Project(TimeAbstract, CommonParent):
    """项目"""

    # area.project
    projectid = models.CharField(max_length=128, db_index=True, unique=True, verbose_name='项目ID',
                                 help_text='前端无须传值')
    name = models.CharField(max_length=100, verbose_name='项目名称')
    alias = models.CharField(max_length=128, default='', verbose_name='项目别名')
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, blank=True, verbose_name="产品线")
    creator = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, verbose_name='项目创建人',
                                help_text='前端不需要传递')
    manager = models.SmallIntegerField(
        blank=True, null=True, verbose_name='项目负责人')
    developer = models.SmallIntegerField(
        blank=True, null=True, verbose_name='开发负责人')
    tester = models.SmallIntegerField(
        blank=True, null=True, verbose_name='测试负责人')
    extra_members = models.JSONField(default=get_default_extra_members,
                                     verbose_name="额外成员组", help_text='{"name": "自定义成员组1", members: [1,2,3]}')
    desc = models.TextField(verbose_name='描述', null=True, blank=True)
    notify = models.JSONField(
        default=dict, verbose_name='消息通知', help_text='{"robot": "robot_name"}')

    def __str__(self):
        return self.name

    class ExtMeta:
        related = True
        dashboard = True
        icon = 'tree-table'

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = verbose_name + '管理'
        default_permissions = ()


class KubernetesCluster(TimeAbstract):
    """
    K8s集群配置
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='集群名称')
    version = models.JSONField(default=dict, verbose_name='版本',
                               help_text='{"core": "1.14", "apiversion": "apps/v1"}\ncore: 集群版本\napiversion: API版本')
    desc = models.TextField(null=True, blank=True, verbose_name='集群描述')
    config = models.JSONField(default=dict, verbose_name='集群配置')
    environment = models.ManyToManyField(
        Environment, related_name='env_k8s', blank=True, verbose_name='环境')
    product = models.ManyToManyField(
        Product, related_name='product_k8s', blank=True, verbose_name='产品')
    idc = models.ForeignKey(Idc, blank=True, null=True,
                            on_delete=models.PROTECT, verbose_name='IDC')

    def __str__(self):
        return self.name

    class ExtMeta:
        related = True
        dashboard = True
        icon = 'k8s'

    class Meta:
        default_permissions = ()
        ordering = ['-id']
        verbose_name = 'K8s集群'
        verbose_name_plural = verbose_name + '管理'


def get_default_value():
    return {
        'key': 'default', 'value': 'default'
    }


# 应用部署方式
G_DEPLOY_TYPE = (
    ('nonk8s', '非Kubernetes部署'),
    ('docker', 'Docker部署'),
    ('k8s', 'Kubernetes部署')
)


G_ONLINE_CHOICE = (
    (0, '未上线'),
    (1, '已上线'),
    (2, '部署中'),
    (3, '部署异常'),
    (9, '已申请上线')
)


class MicroApp(TimeAbstract):
    # product.project.microapp
    appid = models.CharField(max_length=250, db_index=True, unique=True, verbose_name='应用ID',
                             help_text='应用唯一标识，无需填写')
    name = models.CharField(max_length=128, verbose_name='应用')
    alias = models.CharField(max_length=128, blank=True, verbose_name='别名')
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, null=True, blank=True, verbose_name='项目')
    creator = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, verbose_name='创建者',
                                help_text='前端不需要传递')
    repo = models.JSONField(default=dict, verbose_name='仓库地址',
                            help_text='{"name": name, "description": "", "path_with_namespace": "", "http_url_to_repo": url}')
    target = models.JSONField(default=get_default_value, verbose_name='JAR包配置',
                              help_text='默认：default, {"default": "default", "custom": "xxx/a.war"}')
    extra_members = models.JSONField(default=get_default_extra_members,
                                     verbose_name="额外成员组", help_text='{"name": "自定义成员组1", members: [1,2,3]}')
    category = models.CharField(
        max_length=128, blank=True, null=True, verbose_name='应用分类')
    template = models.JSONField(default=dict, verbose_name='K8sDeployment模板',
                                help_text='Kubernetes Deployment部署模板配置')
    language = models.CharField(
        max_length=32, default='java', verbose_name='开发语言')
    multiple_app = models.BooleanField(
        default=False, blank=True, verbose_name='多应用标志')
    multiple_ids = models.JSONField(default=list, verbose_name='多应用关联ID列表')
    dockerfile = models.JSONField(default=get_default_value, verbose_name='Dockerfile配置',
                                  help_text='默认：{default: null}, 可选: {"default|默认": null, "project|使用项目Dockerfile"： "project", "custom|自定义Dockerfile": ""}')
    online = models.BooleanField(default=True, blank=True, verbose_name='上线下线',
                                 help_text='应用上线/下线状态标记, 下线状态的应用禁止发布.')
    desc = models.TextField(verbose_name='描述', null=True, blank=True)
    notify = models.JSONField(default=dict, verbose_name='消息通知')
    can_edit = models.JSONField(default=list, verbose_name='管理人员',
                                help_text='有权限编辑该应用的人员ID\n格式为数组, 如[1,2]')
    is_k8s = models.CharField(max_length=8, default='k8s', choices=G_DEPLOY_TYPE, verbose_name='部署方式',
                              help_text=f'默认k8s, 可选: {dict(G_DEPLOY_TYPE)}')
    modules = models.JSONField(default=list, verbose_name='工程模块')

    def __str__(self):
        return '[%s]%s' % (self.name, self.alias)

    class ExtMeta:
        related = True
        dashboard = True
        icon = 'component'

    class Meta:
        default_permissions = ()
        ordering = ['-created_time']
        verbose_name = '应用'
        verbose_name_plural = verbose_name + '管理'


class AppInfo(TimeAbstract):
    # uniq_tag: product.project.microapp.env
    uniq_tag = models.CharField(
        max_length=128, unique=True, verbose_name='唯一标识', help_text='前端留空，无需传值')
    app = models.ForeignKey(MicroApp, blank=True, null=True,
                            on_delete=models.PROTECT, verbose_name='应用')
    environment = models.ForeignKey(
        Environment, on_delete=models.PROTECT, null=True, verbose_name='环境')
    branch = models.CharField(
        max_length=64, blank=True, null=True, verbose_name="默认构建分支")
    allow_ci_branch = models.JSONField(default=list, verbose_name='允许构建的分支',
                                       help_text="存储数组格式，具体的分支名; 默认['*'], 表示允许所有分支.")
    allow_cd_branch = models.JSONField(default=list, verbose_name='允许发布的分支',
                                       help_text="存储数组格式，具体的分支名; 默认['*'], 表示允许所有分支.")
    build_command = models.CharField(max_length=250, blank=True, null=True, verbose_name='构建命令',
                                     help_text='根据应用开发语言, 从getKey("LANGUAGE")获取数据, 取出extra字段的build值')
    kubernetes = models.ManyToManyField(KubernetesCluster, related_name='k8s_app', through='KubernetesDeploy',
                                        verbose_name='K8s集群')
    hosts = models.JSONField(
        default=list, verbose_name='部署主机', help_text='部署主机, 格式: []')
    template = models.JSONField(default=dict, verbose_name='K8sDeployment模板',
                                help_text='继承自当前应用的template字段,数据格式为对象\n字段说明:\ntype: 0|1, 0表示继承应用模板,template为空字典;1表示自定义模板\n示例: {"type": 0, "template": {}}')
    # {0: 禁用， 1： 启用}
    is_enable = models.SmallIntegerField(
        default=1, verbose_name='启用', help_text='状态 {0: 禁用， 1： 启用}，默认值为1')
    desc = models.TextField(verbose_name='描述', null=True, blank=True)
    can_edit = models.JSONField(default=list, verbose_name='管理人员',
                                help_text='有权限编辑该应用的人员ID\n格式为数组, 如[1,2]')
    online = models.SmallIntegerField(default=0, choices=G_ONLINE_CHOICE, verbose_name='是否上线',
                                      help_text=f'默认为0,即未上线\n可选项: {G_ONLINE_CHOICE}')

    def __str__(self):
        return self.uniq_tag

    @property
    def namespace(self):
        return f'{self.environment.name.replace("_", "-")}-{self.app.project.name.replace("_", "-")}'.lower()

    @property
    def jenkins_jobname(self):
        try:
            job_name = f'{self.environment.name}-{self.app.category.split(".")[-1]}-{self.app.project.name}-{self.app.name.split(".")[-1]}'.lower(
            )
        except AppInfo.DoesNotExist:
            job_name = ''
        return job_name

    class ExtMeta:
        related = True
        dashboard = True

    class Meta:
        default_permissions = ()
        ordering = ['-update_time', '-id']
        verbose_name = '应用模块'
        verbose_name_plural = verbose_name + '管理'


class KubernetesDeploy(TimeAbstract):
    appinfo = models.ForeignKey(
        AppInfo, related_name='app_info', null=True, on_delete=models.CASCADE)
    kubernetes = models.ForeignKey(
        KubernetesCluster, related_name='app_k8s', null=True, on_delete=models.CASCADE)
    online = models.SmallIntegerField(default=0, choices=G_ONLINE_CHOICE, verbose_name='是否上线',
                                      help_text=f'默认为0,即未上线\n可选项: {G_ONLINE_CHOICE}')
    version = models.CharField(
        max_length=250, blank=True, null=True, verbose_name='当前版本')

    def __str__(self):
        return '%s-%s' % (self.appinfo.app.appid, self.kubernetes.name)

    class Meta:
        default_permissions = ()
