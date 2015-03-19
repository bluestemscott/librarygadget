from urls import *

urlpatterns.extend(patterns('',

    # Static content (local dev only)
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
    {'document_root': os.path.join(SITE_ROOT, 'templates') + '/site_media'}),


))

