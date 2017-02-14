"""tradecore URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token

from social import views


# The convention for urlpatterns and router variables seems to
# be lowercase letters, so pylint isn't really helping here,
# as the names are taken to be valid
# pylint: disable=invalid-name
router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet)
router.register(r'user_profile', views.UserProfileViewSet)
router.register(r'post', views.PostViewSet)
router.register(r'like', views.LikeViewSet, base_name='like')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/login/', obtain_jwt_token),
    url(r'^api/v1/', include(router.urls)),
    url(r'^api-docs/', include('rest_framework.urls', namespace='rest_framework'))
]
