from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q

from paypal.standard.ipn.signals import payment_was_successful

import os
import base64
import hashlib
import logging
import datetime
import json

import librarybot.gmail
import horizon
import polaris
import sirsidynix
import opac
import webpacpro
import koha

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    api_key = models.CharField(max_length=128, null=True, blank=True)
    ACCOUNT_LEVEL = (
        ('free', 'Free'),
        ('paid', 'Paid')
    )
    account_level = models.CharField(max_length=10, choices=ACCOUNT_LEVEL,  default='free')

    def get_patrons(self):
        patrons = Patron.objects.filter(user=self.user)
        patrons = patrons.filter(inactive=False)
        #patrons = patrons.order_by('library', 'patronid')
        return patrons

    def get_patron_by_id(self, patronid):
        patrons = Patron.objects.filter(user=self.user)
        patrons = patrons.filter(inactive=False)
        patrons = patrons.filter(patronid=patronid)
        #patrons = patrons.order_by('library', 'patronid')
        if len(patrons) == 0:
            logging.warn('No patrons found with id ' + patronid)
            return None
        return patrons[0]

    def create_api_key(self):
        self.api_key = base64.b32encode(os.urandom(32)).strip('=')


class Library(models.Model):
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    regional_system = models.ForeignKey('self', default=None, null=True, blank=True)
    catalogurl = models.URLField(null=True, blank=True)
    LIBRARY_SYSTEMS = (
        ('ipac', 'Horizon'),
        ('webpacpro', 'WebPac Pro'),
        ('opac', 'Opac'),
        ('sirsidynix', 'Sirsi Dynix'),
        ('polaris', 'Polaris'),
        ('koha', 'Koha')
    )
    librarysystem = models.CharField(max_length=20, choices=LIBRARY_SYSTEMS, null=True, blank=True)
    RENEW_SUPPORTED = (
        ('tested', 'Tested'),
        ('unavailable', 'Unavailable'),
        ('untested', 'Untested')
    )
    renew_supported_code = models.CharField(max_length=10, choices=RENEW_SUPPORTED, default='untested')
    active = models.BooleanField(default=True)
    lastmodified = models.DateField(auto_now=True)
    pin_required = models.BooleanField(default=True)

    def get_absolute_url(self):
        return "/library/%i/" % self.id

    def __str__(self):
        return self.name

    def get_catalog_url(self):
        if self.regional_system is not None:
            return self.regional_system.catalogurl
        return self.catalogurl

    def get_library_system(self):
        if self.regional_system is not None:
            return self.regional_system.librarysystem
        return self.librarysystem


class Patron(models.Model): 
    library = models.ForeignKey(Library)
    user = models.ForeignKey(User, null=True) #Patrons aren't required to have a User (yet)
    patronid = models.CharField(max_length=40, verbose_name='Library card number')
    pin = models.CharField(max_length=75, verbose_name='Library website password')
    name = models.CharField(max_length=150, null=True, blank=True, verbose_name='Name on library card')
    save_history = models.BooleanField()
    lastchecked = models.DateTimeField(auto_now=False)
    batch_last_run = models.DateField(null=True, blank=True)
    inactive = models.BooleanField()

    #def __str__(self):
    #	return self.patronid

    def get_bot(self, password='', name=''):
        password = password.strip()
        name = name.strip()

        logging.debug("get_bot for %s (%s) using %s" % (self.library.name, self.library.get_catalog_url(), self.library.get_library_system()))
        if self.library.get_library_system() == 'ipac':
            return horizon.LibraryBot(self.library.get_catalog_url(), self.patronid, password, name)
        if self.library.get_library_system() == "sirsidynix":
            return sirsidynix.LibraryBot(self.library.get_catalog_url(), self.patronid, password, name)
        if self.library.get_library_system() == 'opac':
            return opac.LibraryBot(self.library.get_catalog_url(), self.patronid, password, name)
        if self.library.get_library_system() == 'webpacpro':
            return webpacpro.LibraryBot(self.library.get_catalog_url(), self.patronid, password, name)
        if self.library.get_library_system() == 'polaris':
            return polaris.LibraryBot(self.library.get_catalog_url(), self.patronid, password, name)
        if self.library.get_library_system() == 'koha':
            return koha.LibraryBot(self.library.get_catalog_url(), self.patronid, password, name)

    def items_out(self, password, patron_name):
        bot = self.get_bot(password, patron_name)
        checkedout = []
        checkedout = bot.itemsOut()
        checkedoutlist = checkedout.values();
        #print "json=" + json.dumps(checkedoutlist, cls=domain.ItemEncoder)
        checkedoutlist.sort(key=lambda item: (item.dueDate, item.title))
        return checkedoutlist


    def get_items(self, password, name, asof_date, check_cache=True, lastchecked_jscompat=True):
        # get items from cache
        asof_date = asof_date.replace(microsecond=0)
        if check_cache == True:
            if password == self.pin:
                if asof_date<=self.lastchecked:
                    # return as a list not QuerySet to make JSON serialization consistent
                    items = Item.objects.filter(patron=self, asof=asof_date.date())
                    #turn the django query result into a regular list
                    item_list = []
                    item_list.extend(items)
                    logging.info('returning cached items of length: ' + str(len(items)))
                    return item_list
            else:
                logging.warn('password does not match for %s', self.patronid)


        # get items from library and update cache
        items = self.items_out(password, name)
        logging.info('remote library call for patron ' + self.patronid + ' items len=' + str(len(items)) + ' asof_date=' + str(asof_date) + ' self.lastchecked=' + str(self.lastchecked))
        if lastchecked_jscompat: # google gadget expected to control the asof_date
            self.lastchecked = asof_date
        else: #website does not
            self.lastchecked = datetime.datetime.now()
        self.save()
        self.update_items(items, asof_date.date())
        return items

    def get_items_max_cache(self):
        midnight = datetime.datetime.now()
        midnight = midnight.replace(hour=0, minute=0)
        return self.get_items(password=self.pin, name=self.name, asof_date=midnight, lastchecked_jscompat=False)

    def get_items_fresh(self):
        midnight = datetime.datetime.now()
        midnight = midnight.replace(hour=0, minute=0)
        return self.get_items(password=self.pin, name=self.name, asof_date=datetime.datetime.now(), check_cache=False, lastchecked_jscompat=False)

    def renew_items(self, password, name, titles):
        bot = self.get_bot(password, name)
        renewedItems = []
        renewedItems = bot.renew(titles)
        renewedItemsList = renewedItems.values();
        renewedItemsList.sort(key=lambda obj:obj.dueDate)
        self.update_items(renewedItemsList, datetime.date.today())
        return renewedItemsList

    def update_items(self, items, asof=datetime.date.today()):
        if self.save_history == False:
            Item.objects.filter(patron=self).delete()
        for item in items:
            logging.debug(item.title)
            item.asof = datetime.date.today()
            item.id
            item.patron = self
            item.save()



class Item(models.Model):
    patron = models.ForeignKey(Patron)
    title = models.CharField(max_length=1024)
    author = models.CharField(max_length=1024, null=True, blank=True)
    outDate =  models.DateField(null=True, blank=True)
    dueDate = models.DateField(null=True, blank=True)
    timesRenewed = models.SmallIntegerField(null=True, blank=True)
    isbn = models.CharField(max_length=25, null=True, blank=True)
    asof = models.DateField()

    # These fields are transient and shouldn't be persisted to DB
    renewitemkeys = None
    renewalError = None
    renewed = None
    renewable = None
    renew_url = None


class AccessLog(models.Model):
    user = models.ForeignKey(User, editable=False)
    patron = models.ForeignKey(Patron, editable=False)
    library = models.ForeignKey(Library, editable=False)
    renewed_count = models.IntegerField(null=True)
    almost_due_count = models.IntegerField(null=True)
    overdue_count = models.IntegerField(null=True)
    viewfunc = models.CharField(max_length=50)
    error = models.CharField(max_length=150, null=True, blank=True)
    error_stacktrace = models.CharField(max_length=3000, null=True, blank=True)
    date = models.DateField(auto_now=True, null=True)


class LibraryRequest(models.Model):
    user = models.ForeignKey(User, editable=False, null=True) #added later, so making it nullable for easier migration
    libraryname = models.CharField('Name of library', blank=False, max_length=200)
    catalogurl = models.CharField('Library account web page', blank=False, max_length=200) #help_text='Usually you can find this by clicking "My Account" on your library\'s web site.  Then copy and paste the URL here.'
    name = models.CharField('Name on library card', max_length=60, blank=True)
    patronid = models.CharField('Card number', max_length=40, blank=True)
    password = models.CharField('Library web site password',  max_length=20, blank=True)
    renewal_item = models.CharField('Title to test renewals with', max_length=150, blank=True)
    date = models.DateTimeField(auto_now=True)


class RenewalResponse(models.Model):
    token = models.CharField(max_length=36)
    response = models.TextField()
    cachedate = models.DateTimeField(auto_now=True)


def get_patron(library_id, account_id, password, patron_name):
    patron_library = Library.objects.filter(id=library_id)[0]
    patron = None
    account_id = account_id.strip()
    patrons = Patron.objects.filter(library=patron_library, patronid=account_id)
    if len(patrons) == 0:
        patron = Patron(library=patron_library, patronid=account_id, pin=password, save_history=False)
        patron.id
        patron.lastchecked = datetime.datetime.now().replace(year=2000) # lastchecked can't be null but we want it to be in the past
        patron.save()
    else:
        patron = patrons[0]

    return patron

class Pricing():
    annual_cost = 4.99


def test_site(request):
    return request.META['SERVER_PORT'] == '8000' or request.user.username == 'scollyp@gmail.com'

# receives paypal ipn signals	
def paypal_ipn_success(sender, **kwargs):
    ipn_obj = sender
    # upgrade the user to paid status
    username = ipn_obj.custom
    user = User.objects.get(username__exact=username)
    user_profile = user.get_profile()
    user_profile.account_level = 'paid'
    user_profile.save()

    librarybot.gmail.send_message(user.email,
        'Library Gadget payment confirmation',
        'Thank you for activating your Library Gadget 1 year premium account. Your confirmation number is ' + ipn_obj.txn_id + '. Welcome to library peace of mind!')

payment_was_successful.connect(paypal_ipn_success)



class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Library):
            json_result = obj.__dict__
            json_result['lastmodified'] = str(obj.lastmodified)
            json_result['_state'] = ''
            return json_result

        if isinstance(obj, Patron):
            json_result = obj.__dict__
            json_result['_state'] = ''
            json_result['_patron_cache'] = ''
            json_result['lastchecked'] = ''
            json_result['batch_last_run'] = ''
            return json_result

        if isinstance(obj, Item):
            json_result = obj.__dict__
            json_result['_state'] = ''
            json_result['outDate'] = str(obj.outDate)
            json_result['dueDate'] = str(obj.dueDate)
            json_result['asof'] = str(obj.asof)
            return json_result

        return json.JSONEncoder.default(self, obj)

