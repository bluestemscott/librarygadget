from django.conf.urls.defaults import *

urlpatterns = patterns('librarybot.viewsapi',
    # UI
    url(r'^library/(?P<library_id>\d+)/(?P<account_id>\w+)/items/(?P<asof_date>\w+).json/$', 'items_out_json', name='librarybotitems'),
    url(r'^userprofile/(?P<api_key>\w+)/items/$', 'checked_out_json'),
    url(r'^libraries.json/$', 'library_list_json', name='librarybotlibraries'),
    url(r'^renewal/(?P<reqToken>\w+)/$', 'renew_items', name='librarybotrenewal'),
    url(r'^renewalResponse/(?P<reqToken>\w+)/$', 'get_renewal_response', name='librarybotrenewalresponse'),
    url(r'^userprofile/(?P<api_key>\w+)/patrons/$', 'get_patrons_from_key'),
    url(r'^user/patrons/$', 'get_patrons_from_user'),

    url(r'^$', 'index', name='librarybotindex'),
)

