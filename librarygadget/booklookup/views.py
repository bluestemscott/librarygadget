import urllib
import httplib2

from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseRedirect

import amazon
import json
import logging
import traceback

@cache_page(60*10)		
def amazon_json(request, title, author=''):
    result = amazon.item_lookup(title, author)
    if result.imageurl == None:
        result.imageurl = 'http://www.librarygadget.com/images/noimage_available.png'
    #result.short_itemurl = shorten_url(result.itemurl)
    jsonresponse = json.dumps(result.__dict__)
    response = HttpResponse(jsonresponse)
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response

@cache_page(60*10)
def amazon_redirect(request):
    title = request.GET.get('title','')
    author = request.GET.get('author','')
    result = amazon.item_lookup(title, author)
    if result is None or result.itemurl is None:
        return HttpResponseRedirect(''.join(
            ["http://www.amazon.com/gp/search?ie=UTF8&tag=librgadg-20&index=blended&linkCode=ur2&camp=1789&creative=9325&",
             urllib.urlencode({'keywords': title})]))

    return HttpResponseRedirect(result.itemurl)


@cache_page(60*10)
def amazon_image(request, size):
    title = request.GET.get('title','')
    author = request.GET.get('author','')
    result = amazon.item_lookup(title, author)
    if result is None or result.itemurl is None:
        return HttpResponseRedirect('/images/none.jpg')

    if size == 'small':
        return HttpResponseRedirect(result.small_image_url)
    if size == 'large':
        return HttpResponseRedirect(result.large_image_url)

    return HttpResponseRedirect(result.medium_image_url)


