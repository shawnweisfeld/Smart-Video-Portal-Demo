"""
Definition of urls for djangoapp.
"""

from datetime import datetime
from django.conf.urls import url
import django.contrib.auth.views

import app.forms
import app.views

# Uncomment the next lines to enable the admin:
# from django.conf.urls import include
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = [
    # Examples:
    url(r'^$', app.views.home, name='home'),  
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^upload/', app.views.upload_file, name='upload'),
    url(r'^render/', app.views.render_video, name='render'),
    url(r'^rendered/', app.views.rendered_video, name='rendered'),     
    url(r'^videos/', app.views.videos, name='videos'),     
    url(r'^video/([0-9]{8}\.[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12})/$', app.views.video, name='video'),
    url(r'^translate/', app.views.translate, name='translate'),
    url(r'^speak/', app.views.speak, name='speak'),
]
