from django.conf.urls.defaults import *
from django.contrib import admin
import django
import os
import django.contrib.auth.views

# Django settings for djangolibrarybot project.
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

admin.autodiscover()

urlpatterns = patterns('',

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^librarybot/', include('librarybot.urlsapi')),	
    (r'^booklookup/', include('booklookup.urls')),
    (r'^share/', include('share.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^', include('librarybot.urlsui')),

    # Paypal
     (r'^ipny283fih92$', include('paypal.standard.ipn.urls')),

    # Registration
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    url(r'^accounts/profile/$', 'librarybot.viewsui.profile'),

    # Home page
    url(r'^$', 'librarybot.viewsui.home', name='home'),

)
