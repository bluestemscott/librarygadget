import datetime
import locale
import logging
import random
import traceback
import urllib

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.conf import settings
import django.forms as forms
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from librarybot import util, gmail
from librarybot.util import LoginException

from paypal.standard.forms import PayPalPaymentsForm

import librarybot.models as models
from librarybot.models import Library
from librarybot.models import AccessLog
from librarybot.models import Patron

def log_exception(request, patron, viewfunc, exception):
    logging.error(' '.join([request.path, str(exception), traceback.format_exc().strip()[0:2999]]))
    if patron is not None:
        accessLog = AccessLog()
        accessLog.patron = patron
        accessLog.library = patron.library
        accessLog.viewfunc = viewfunc
        accessLog.error = str(exception)
        accessLog.error_stacktrace = traceback.format_exc().strip()[0:2999]
        accessLog.save()

# general / unsecured views							

def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('checkedout')
    return render_to_response('home.html',
                              context_instance=RequestContext(request))

def error(request):
    return render_to_response('error.html', context_instance=RequestContext(request))

def privacy(request):
    return render_to_response('privacy.html', context_instance=RequestContext(request))

def about(request):
    return render_to_response('about.html', context_instance=RequestContext(request))

def terms_of_use(request):
    return render_to_response('termsofuse.html', context_instance=RequestContext(request))

@login_required
def checked_out(request):
    user_profile = request.user.get_profile()
    patrons = user_profile.get_patrons()

    items = []
    account_problems = []
    for patron in patrons:
            try:
                items.extend(patron.get_items_max_cache())
            except LoginException:
                account_problems.append(patron)
            except Exception as e:
                account_problems.append(patron)
                log_exception(request, patron, 'checkedout', e)

    items.sort(key=lambda item: (item.dueDate, item.title))
    for item in items:
        item.short_title = item.title[0:69]
        if len(item.title) >= 70:
            item.short_title = item.short_title + "..."
        author = item.author
        if author is None:
           author = ''
        item.amazon_url = ''.join(["http://www.librarygadget.com/booklookup/amazon/redirect/?title=",
                                   urllib.quote_plus(item.title),
                                   "&author=",
                                   urllib.quote_plus(author)])
        item.overdue =  item.dueDate <= datetime.date.today()


    message = ''
    if len(items) == 0 and len(account_problems) == 0 and len(patrons) > 0:
        message = "You don't have anything checked out. Quick! Go to the library!"

    return render_to_response('checkedout.html',
        {'items':items,
         'patrons':account_problems, #naming this "patrons" to reuse useraccounts.html - ugly
         'return':request.path,
         'all_patrons': patrons,
         'free': user_profile.account_level == 'free',
         'message': message},
        context_instance=RequestContext(request))


class LibraryForm(forms.ModelForm):
    class Meta:
        model = Library

def libraries(request):
    libraries = Library.objects.filter(active=True)
    libraries = libraries.order_by('state', 'name')
    return render_to_response('libraries.html',
        {'libraries':libraries},
        context_instance=RequestContext(request))


def pricing_plans(request):
    total_cost = models.Pricing.annual_cost
    return render_to_response('pricingplans.html',
                            {'total_cost': locale.currency(total_cost),
                             },
                            context_instance=RequestContext(request))

# Registration and account maintenance views


class RegistrationForm(forms.Form):
    email = forms.EmailField(required=True, error_messages={'required': 'Please enter your email address.'})
    password = forms.CharField(required=True, error_messages={'required': 'Please enter a password'})
    terms_of_use = forms.BooleanField(error_messages={'required': 'Agree to the Terms of Use in order to create an account.'})

    def clean_email(self):
        data = self.cleaned_data['email']
        if len(User.objects.filter(username=data)) > 0:
            raise forms.ValidationError('Username already in use.')
        return data

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(email, email, password)
            user_profile = models.UserProfile(user=user)
            user_profile.create_api_key()
            user_profile.save()
            user = authenticate(username=email, password=password)
            if user != None:
                login(request, user)
                return HttpResponseRedirect('profile')
            #some bizarre error happened
            return HttpResponseRedirect('error')
    else:
        form = RegistrationForm()
        request.session['plan'] = request.GET.get('plan', 'free')
    return render_to_response('registration/register.html',
                            {'form' : form,
                             'total_cost' : locale.currency(models.Pricing.annual_cost)},
                            context_instance=RequestContext(request))

@login_required							
def profile(request):
    user_profile = request.user.get_profile()
    patrons = user_profile.get_patrons()
    upgrade = create_upgrade(request)

    if request.session.get('plan', 'free') == 'premium' and user_profile.account_level != 'paid':
        return render_to_response('initialpayment.html',
                {'upgrade': upgrade,},
                 context_instance=RequestContext(request))

    return render_to_response('profile.html',
        {'patrons': patrons,
         'upgrade': upgrade,
         'free': user_profile.account_level == 'free',
         'return':request.path},
        context_instance=RequestContext(request))


class PatronForm(forms.ModelForm):
    class Meta:
        model = Patron
        fields = ('name', 'patronid', 'pin')

@login_required
def add_account(request, library_id):
    library = Library.objects.get(pk=library_id)
    if request.method == 'POST':
        patron_form = PatronForm(request.POST)
        if patron_form.is_valid():
            patron = patron_form.save(commit=False)
            patron.user = request.user
            patron.library = library
            patron.save_history = False
            patron.lastchecked = datetime.datetime.min
            patron.inactive = False
            patron.save()
            return HttpResponseRedirect('add')
    patron_form = PatronForm()
    user_profile = request.user.get_profile()
    patrons = user_profile.get_patrons()
    return render_to_response('libraryaccount.html',
        {'form': patron_form,
        'library': library,
        'patrons': patrons,
        'free': user_profile.account_level == 'free',
        'upgrade': create_upgrade(request),
        'return': request.path},
        context_instance=RequestContext(request))


@login_required
def delete_account(request):
    if request.method == 'POST':
        patronid = request.POST['patronid']
        user_profile = request.user.get_profile()
        patron = user_profile.get_patron_by_id(patronid)
        if patron == None:
            raise Exception('No patron found for patronid ' + patronid)
        patron.inactive = True
        patron.save()
        return HttpResponseRedirect(request.POST['return'])


def create_upgrade(request):
    test_account = models.test_site(request)
    user_profile = request.user.get_profile()
    patrons = user_profile.get_patrons()

    total_cost = models.Pricing.annual_cost
    if test_account:
        total_cost = .5
    invoice_number = random.randint(10000, 1000000000)
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": str(total_cost),
        "item_name": "Library Gadget Premium (1 year)",
        "invoice": str(invoice_number),
        "notify_url": "http://www.librarygadget.com/ipny283fih92",
        "return_url": "http://www.librarygadget.com/order/return",
        "cancel_return": "http://www.librarygadget.com/profile",
        "custom": request.user.username
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    return  {'test_paypal': test_account,
             'total_cost': locale.currency(total_cost),
            'form': form}

@login_required
@csrf_exempt
def paypal_order_return(request):
    if request.GET['st'] != 'Completed':
        # not sure whether this is possible or not
        return HttpResponseRedirect('error')

    paypal_order = {}
    paypal_order['tx'] = request.GET['tx']

    return render_to_response('orderreturn.html',
        {'paypal_order': paypal_order},
        context_instance=RequestContext(request))

class LibraryRequestForm(forms.ModelForm):
    class Meta:
        model = models.LibraryRequest


@login_required
def library_request(request):
    if request.method == 'POST':
        form = LibraryRequestForm(request.POST)
        if form.is_valid():
            library_request = form.save(commit=False)
            library_request.user = request.user
            library_request.save()
            gmail.send_message('scott@librarygadget.com',
                'New library request',
                'Take a look... ')

            return HttpResponseRedirect('libraryrequestthanks')
    else:
        form = LibraryRequestForm()
    return render_to_response('libraryrequest.html',
        {'form': form,},
        context_instance=RequestContext(request))

def library_request_thanks(request):
    return render_to_response('libraryrequestthanks.html',
        context_instance=RequestContext(request))