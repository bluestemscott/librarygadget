import unittest
import json
import logging
import datetime

from django.test.client import Client
from django.test import TestCase

import librarybot.models as models
import librarybot.tests
from librarybot.models import AccessLog


today = datetime.date.today()
date_str = datetime.date.strftime(today, '%Y%m%d')
url = '/librarybot/library/3/21704005627502/items/' + date_str + 'T010000.json/'

def items_out_exception(self, password, patron_name):
    print "raising exception"
    raise Exception("fake exception")

def items_out_mock(self, password, patron_name):
    items = []
    items.append(models.Item(title='Love in the Ruins', dueDate=today))
    items.append(models.Item(title='Bugs Bunny', dueDate=today))
    return items
        		
class JsonApi(TestCase):
    fixtures = ['libraries']
    user = None

    def setUp(self):
        self.user = librarybot.tests.create_user('scott', 'test')
        librarybot.tests.create_patron(self.user, 3, '21704005627502', '4042')

    def test_library_list_json(self):
        c = Client()
        response = c.get('/librarybot/libraries.json/')
        libraries = json.loads(response.content)
        self.assertTrue(len(libraries)>0)
        library = [lib for lib in libraries if lib['id'] == 3][0]
        self.assertEquals('Des Moines Public Library', library['name'])
        self.assertEquals('IA', library['state'])

    def test_exception(self):
        logging.debug('about to call')
        c = Client()
        models.Patron.items_out = items_out_exception
        response = c.get(url, {'password':'4042', 'name':'Scott'})

        logging.debug('response=' + response.content)
        logs = AccessLog.objects.all()
        self.assertTrue(len(logs) > 0)
        print logs

    def test_login_twice(self):
        logging.debug('about to call')
        c = Client()

        models.Patron.items_out = items_out_mock
        response = c.get(url, {'password':'4042', 'name':'Scott'})
        #print response.content
        items = json.loads(response.content)['items']
        self.assertEquals(2, len(items))

        response = c.get(url, {'password':'4042', 'name':'Scott'})
        items = json.loads(response.content)['items']
        self.assertEquals(2, len(items))

    def test_api_key(self):
        c = Client()
        response = c.get('/librarybot/user/patrons/', {'username':'scott', 'password':'test'})
        print response.content
        self.assert_patrons_response(response)

    def test_api_key_bad_password(self):
        c = Client()
        response = c.get('/librarybot/user/patrons/', {'username':'blah', 'password':'fake'})
        error = json.loads(response.content)['servererror']
        self.assertEquals('Authentication failed for blah', error)

    def test_get_patrons(self):
        user_profile = self.user.get_profile()
        c = Client()
        response = c.get('/librarybot/userprofile/' + user_profile.api_key + '/patrons/')
        self.assert_patrons_response(response)

    def assert_patrons_response(self, response):
        #print response.content
        patrons = json.loads(response.content)['patrons']
        patron = patrons[0]
        self.assertEquals('21704005627502', patron['patronid'])
        self.assertEquals('4042', patron['pin'])
        self.assertEquals(3, patron['library_id'])
        api_key = json.loads(response.content)['api_key']
        self.assertTrue(len(api_key)>0)

def suite():
    return unittest.TestSuite((unittest.makeSuite(JsonApi,'test')))

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

