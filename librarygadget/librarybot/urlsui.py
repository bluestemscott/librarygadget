from django.conf.urls.defaults import *

urlpatterns = patterns('librarybot.viewsui',
    # UI
    url(r'^libraries$', 'libraries', name='libraries'),
    url(r'^privacy$', 'privacy', name='privacy'),
    url(r'^about$', 'about', name='about'),
    url(r'^checkedout$', 'checked_out', name='checked_out'),
    url(r'^profile$', 'profile', name='profile'),
    url(r'^pricingplans$', 'pricing_plans', name='pricing_plans'),
    url(r'^termsofuse$', 'terms_of_use', name='terms_of_use'),
    url(r'^register$', 'register', name='register'),
    url(r'^libraryrequest$', 'library_request', name='library_request'),
    url(r'^libraryrequestthanks$', 'library_request_thanks', name='library_request_thanks'),
    url(r'^order/return$', 'paypal_order_return', name='paypal_order_return'),
    url(r'^libraryaccount/delete$', 'delete_account', name='delete_account'),
    url(r'^libraryaccount/(?P<library_id>\d+)/add$', 'add_account', name='add_account'),
)

