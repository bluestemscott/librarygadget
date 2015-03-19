from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect
from django.http import HttpResponse
import logging
import urllib
import models
import bitly

@never_cache		
def facebook_share(request):
	url = request.GET['u']
	title = urllib.unquote(request.GET['t'])
	facebookurl = 'http://www.facebook.com/sharer.php?u=%s' % (url) 
	#logging.debug('Sharing %s on Facebook' % (title))
	share = models.ShareEvent()
	share.linktitle = title
	share.linkurl = url
	share.sharesystem = 'facebook'
	share.save()
	return HttpResponseRedirect(facebookurl)

@never_cache
def twitter_share(request):
	logging.warn("raw title: %s" % (request.GET['t']))
	title = urllib.unquote(request.GET['t'])
	# apostrophes become %27 so I'm just going to remove them.  What a hack.
	title = title.replace("'", "")
	logging.warn("unquoted and formatted title: %s" % (title))
	url = urllib.unquote(request.GET['u'])
	url = shorten_url(url)
	
	param = urllib.quote_plus("%s - %s" % (title, url), "/:!?'\"%@")
	logging.warn("param: %s" % (param))
	twitterurl = 'http://www.twitter.com?status=%s' % (param) 
	#logging.debug('Sharing %s on Twitter' % (title))
	share = models.ShareEvent()
	share.linktitle = title
	share.linkurl = url
	share.sharesystem = 'twitter'
	share.save()
	response = HttpResponse()
	response['Location'] = twitterurl
	response.status_code = 302
	return response
	
def shorten_url(url):
	api = bitly.Api(login='bluestem', apikey='R_a8bc9556d410b1bf8c29be50075003d5') 
	return api.shorten(url)