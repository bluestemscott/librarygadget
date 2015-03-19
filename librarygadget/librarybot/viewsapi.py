import librarybot.models as models
from librarybot.models import Library
from librarybot.models import LibraryRequest
from librarybot.models import AccessLog
from librarybot.models import RenewalResponse
from librarybot.models import Patron
from librarybot.models import UserProfile
from librarybot.models import JsonEncoder

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import render_to_response
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse

import hashlib
import json
import logging
import traceback
import urllib2
import util
import time
import datetime


def index(request):
    return HttpResponse('Welcome to LibraryBot')



def library_list_json(request):
    try:
        libraries = Library.objects.filter(active=True)
        libraries = libraries.order_by('state', 'name')
        jsonresponse = json.dumps(list(libraries), cls=JsonEncoder)
        response = HttpResponse(jsonresponse)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        return handle_exception(request, None, 'library_list_json', e)



@cache_page(60 * 60 * 12)		
def items_out_json(request, library_id, account_id, asof_date):
    patron_name = ''
    if 'name' in request.GET:
        patron_name = request.GET['name']
    password = ''
    if 'password' in request.GET:
        password = request.GET['password']
    asof_date = datetime.datetime.strptime(asof_date, '%Y%m%dT%H%M%S')
    patron = models.get_patron(library_id, account_id, password, patron_name)

    try:
        items = patron.get_items(password=password, name=patron_name, asof_date=asof_date, check_cache=True, lastchecked_jscompat=True)
        response = {}
        response['asof'] = str(patron.lastchecked)
        response['items'] = items
        jsonresponse = json.dumps(response, cls=JsonEncoder)
        response = HttpResponse(jsonresponse)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        return handle_exception(request, patron, 'items_out_json', e)

@cache_page(60 * 60)
def checked_out_json(request, api_key):
    try:
        user_profile = UserProfile.objects.get(api_key=api_key)
        patrons = user_profile.get_patrons()
        items = []
        for patron in patrons:
            items.extend(patron.get_items_max_cache())
        items.sort(key=lambda item: (item.dueDate, item.title))
        response = {}
        response['items'] = items
        json_response = json.dumps(response, cls=JsonEncoder)
        response = HttpResponse(json_response)
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        return handle_exception(request, None, 'checked_out', e)

@csrf_exempt #google desktop POSTs without csrf token
@never_cache
def renew_items(request, reqToken=None):
    titles = []
    index = 0
    while 'title'+str(index) in request.REQUEST:
        titles.append(request.REQUEST['title'+str(index)])
        index = index+1

    patron_name = ''
    if 'name' in request.REQUEST:
        patron_name = request.REQUEST['name']
    password = ''
    if 'password' in request.REQUEST:
        password = request.REQUEST['password']

    patron = models.get_patron(request.REQUEST['libraryid'], request.REQUEST['patronid'], password, patron_name)

    try:
        response = {}
        response['items'] = patron.renew_items(password, patron_name, titles)
        response['versions'] = versions
        jsonresponse = json.dumps(response, cls=JsonEncoder)

        # should we return response instead of storing it for future retrieval?
        if reqToken == None:
            response = HttpResponse(jsonresponse)
            response['Content-Type'] = 'application/json; charset=utf-8'
            return response

        renewalResponse = RenewalResponse(token=reqToken, response=jsonresponse)
        renewalResponse.id
        renewalResponse.save()

        responsetoken = {}
        responsetoken['token'] = reqToken
        response = HttpResponse(json.dumps(responsetoken))
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response
    except Exception as e:
        return handle_exception(request, patron, 'renew_items', e)


@never_cache
def get_renewal_response(request, reqToken):
    renewalResponses = RenewalResponse.objects.filter(token=reqToken)
    if renewalResponses != None and len(renewalResponses) == 1:
        logging.info('returning renewal result for token: ' + reqToken)
        response= HttpResponse(renewalResponses[0].response)
        #renewalResponses[0].delete()
        response['Content-Type'] = 'application/json; charset=utf-8'
        return response

    return HttpResponse('')

@never_cache
def get_patrons_from_user(request):
    try:
        username = request.GET['username']
        password = request.GET['password']
        user = authenticate(username=username, password=password)
        if (user == None):
            return server_error('Authentication failed for ' + username)
        return patrons_response(user.get_profile())
    except Exception as e:
        return handle_exception(request, None, 'get_patrons_from_user', e)

@cache_page(60 * 60 * 12)				
def get_patrons_from_key(request, api_key):
    try:
        user_profile = UserProfile.objects.get(api_key=api_key)
        return patrons_response(user_profile)
    except Exception as e:
        return handle_exception(request, None, 'get_patrons_from_key', e)

def patrons_response(user_profile):
    json_response = {}
    json_response['api_key'] = user_profile.api_key
    patrons = user_profile.get_patrons()
    json_response['patrons'] = list(patrons)
    response_content = json.dumps(json_response, cls=JsonEncoder)
    response = HttpResponse(response_content)
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response

def handle_exception(request, patron, viewfunc, exception):
    logging.error(' '.join([request.path, str(exception), traceback.format_exc().strip()[0:2999]]))
    if patron is not None:
        accessLog = AccessLog()
        accessLog.user = patron.user
        accessLog.patron = patron
        accessLog.library = patron.library
        accessLog.viewfunc = viewfunc
        accessLog.error = str(exception)
        accessLog.error_stacktrace = traceback.format_exc().strip()[0:2999]
        accessLog.save()
    return server_error(str(exception))

def server_error(error_msg):
    logging.error('returning error ' + error_msg)
    error = {}
    error["servererror"] = error_msg
    response = HttpResponse(json.dumps(error))
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response
