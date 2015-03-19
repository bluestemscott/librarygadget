from django.conf.urls.defaults import *

urlpatterns = patterns('booklookup.views',
    url(r'^(?P<title>.+?)/(?P<author>.+?)/amazon.json/$', 'amazon_json', name='booklookupamazon'),
    url(r'^amazon/redirect/$', 'amazon_redirect', name='amazon_redirect'),
    url(r'^amazon/image/(?P<size>.+?)/$', 'amazon_image', name='amazon_image')
)