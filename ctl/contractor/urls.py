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
    url(r'^my_jobs$', views.my_jobs, name="my-jobs"),
    url(r'^job_details/(?P<job_id>[0-9]+)/$', views.job_detail, name='job-detail'),
    url(r'^change_order/(?P<job_id>[0-9]+)/$', views.change_order, name='change-order'),
    url(r'^take_photo/(?P<job_id>[0-9]+)/$', views.job_photo, name='job-photo'),
    url(r'^customer_signature/(?P<job_id>[0-9]+)/$', views.customer_signature, name='customer-signature'),
    
    url(r'^authorise/$', views.authorise, name="contractor-stripe"),
    url(r'^stripe_contractor_callback/$', views.stripe_contractor_callback),
    ]