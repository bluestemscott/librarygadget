import unittest
import json
import datetime
from django.contrib.auth.models import User
from django.core import management
from django.test.client import Client
from django.test import TestCase
from librarybot import util, models

from librarybot.models import Library, Patron
from fixtures import testhorizon
from fixtures import testopac
from fixtures import testsirsidynix
from fixtures import testwebpacpro
from fixtures import testpolaris
from fixtures import testviews
from fixtures import testbatch
from fixtures import testviewsui
from fixtures import testpaypal
from fixtures import testkoha

class LoginFailed(TestCase):
    fixtures = ['libraries']

    def testloginfailed(self):
        libraries = Library.objects.filter(active=True)
        libraries = libraries.order_by('librarysystem', 'name')
        patronid = '9182347897'
        password = '8346'
        name = "Josephus"
        for library in libraries:
            print library.name
            c = Client()
            response = c.get('/librarybot/library/' + str(library.id) + '/' + str(patronid) + '/items/21000101T010000.json/', {'password':password, 'name':name})
            parsed_response = json.loads(response.content)
            error = parsed_response['servererror']
            #testcase.assertEquals('Library login failed', error)
            if error.find('Library login failed') == -1:
                print library.name + ' test failed - ' + error


def create_patron(user, library_id, patron_id, pin, name=''):
    patron = models.Patron()
    patron.user = user
    patron.library = models.Library.objects.get(pk=library_id)
    patron.patronid = patron_id
    patron.pin = pin
    patron.name = name
    patron.save_history = False
    patron.lastchecked = datetime.datetime.min
    patron.inactive = False
    patron.save()
    return patron

def create_user(email, password):
    user = User.objects.create_user(email, email, password)
    user_profile = models.UserProfile(user=user)
    user_profile.create_api_key()
    user_profile.save()
    return user

class AdhocPatron(TestCase):
    fixtures = ['libraries']

    def setUp(self):
        create_user('scott', 'test')

    def test_patron(self):
        user = User.objects.get(username='scott')
        patron = Patron()
        patron.user = user
        patron.inactive = False
        patron.lastchecked = datetime.datetime.now()

        patron.library = Library.objects.get(id=121)
        patron.patronid = '23113003239112'
        patron.pin = '9741'
        patron.name = 'Jeannine S Furukawa'
        patron.save()

        midnight = datetime.datetime.now()
        midnight = midnight.replace(hour=0, minute=0)
        items = patron.get_items(password=patron.pin, name=patron.name, asof_date=midnight, check_cache=False)
        print str(len(items)), " items out"
        for item in items:
            print item.title + ' - ' + str(item.dueDate)
            self.assertTrue(item.title is not None)
            self.assertTrue(item.dueDate is not None)
"""
        renewals = patron.renew_items(password=patron.pin, name=patron.name, titles=['Never a dry moment'])
        for item in renewals:
            print item.title + ' new due date= ' + str(item.dueDate)
            if item.renewed is not None:
               print '      renewed= ' + str(item.renewed)
            if item.renewalError is not None:
               print '      renewalError= ' + item.renewalError
            self.assertTrue(item.title is not None)
            self.assertTrue(item.dueDate is not None)
"""


class MockHttp(util.HttpConversation):
    def __init__(self):
        pass
    def log_history(self, logger, full_trace=False):
        pass
    def post(self, url, data, headers={}):
        pass
    def get(self, url, data='', headers={}):
        pass

mock_http = MockHttp()

def suite():

    suites = [testhorizon.suite(),
            testopac.suite(),
            testsirsidynix.suite(),
            testwebpacpro.suite(),
            testpolaris.suite(),
            testviews.suite(),
            testbatch.suite(),
            testviewsui.suite(),
            testpaypal.suite(),
            testkoha.suite(),
    ]
    return unittest.TestSuite(suites)
    #return endtoendsuite
    #return testviews.suite()




