"""ctl URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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
from django.conf.urls import url

import views

urlpatterns = [
    url(r'^$', views.booking, name="booking"),
    url(r'^booking2/$', views.booking2, name="booking2"),
    url(r'^booking2/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/$', views.booking2, name="booking2d"),
    url(r'^booking3/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/(?P<slot>[a-z]+)/$', views.booking3, name="booking3"),
    url(r'^booking4/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/(?P<slot>[a-z]+)/(?P<contractor_id>[0-9]+)/$', views.booking4, name="booking4"),
    url(r'^booking5/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})/(?P<slot>[a-z]+)/(?P<contractor_id>[0-9]+)/$', views.booking5, name="booking5"),
]