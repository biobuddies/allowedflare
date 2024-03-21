"""
URL configuration for demo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from django.contrib.admin import site
from django.urls import include, path
from rest_framework import routers

from django_allowedflare import AllowedflareLoginView
from . import views

router = routers.DefaultRouter()
router.register(r'api/groups', views.GroupViewSet)
router.register(r'api/users', views.UserViewSet)

urlpatterns = [
    path('admin/login/', AllowedflareLoginView.as_view(), name='admin-login'),
    path('admin/', site.urls),
    path('explore/', include('explorer.urls')),
    path('health/', include('health_check.urls')),
    path('api/', include(router.urls)),
]

urlpatterns += router.urls
