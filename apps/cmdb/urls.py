from django.conf.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from cmdb.views import RegionViewSet, IdcViewSet, ProductViewSet, ProjectViewSet, EnvironmentViewSet, AppInfoViewSet, KubernetesClusterViewSet, MicroAppViewSet


router = DefaultRouter()

router.register('region', RegionViewSet)
router.register('asset/idc', IdcViewSet)
router.register('product', ProductViewSet)
router.register('project', ProjectViewSet)
router.register('environment', EnvironmentViewSet)
router.register('app/service', AppInfoViewSet)
router.register('app', MicroAppViewSet)
router.register('kubernetes', KubernetesClusterViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
]
