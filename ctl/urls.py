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
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

admin.site.site_header = 'Change The Locks Admin'

import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home, name="home"),
    url(r'^tandc/$', views.tandc, name="tandc"),
    url(r'^booking/', include('ctl.booking.urls')),
    url(r'^contractor/', include('ctl.contractor.urls')),
    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^accounts/profile', views.home),
    url(r'^', include('django.contrib.auth.urls')),
    
    url(r'^cancel/$', views.cancel, name="cancel"),
    
    url(r'^send_photo/$', views.send_photo, name='send-photo'),
    
    
    url(r'^fullcalendar/', TemplateView.as_view(template_name="schedule/fullcalendar.html"), name='fullcalendar'),
    url(r'^schedule/', include('schedule.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
