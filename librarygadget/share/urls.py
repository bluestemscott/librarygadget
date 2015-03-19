from django.conf.urls.defaults import *

urlpatterns = patterns('share.views',
	url(r'^facebook/$', 'facebook_share', name='facebookshare'),
	url(r'^twitter/$', 'twitter_share', name='twittershare'),
)