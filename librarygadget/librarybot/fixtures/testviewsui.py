import unittest
from django.test.client import Client
from django.test import TestCase
from librarybot.viewsui import *
import librarybot.models
from librarybot.models import Library
import logging
from django.contrib.auth import authenticate

class Register(TestCase):
    fixtures = ['libraries']

    def test_register_and_pay(self):
        c = Client()
        response = c.get('/pricingplans')
        self.assertEquals('pricingplans.html', response.template[0].name)

        url = '/register'
        response = c.get(url + '?plan=premium')
        self.assertEquals('registration/register.html', response.template[0].name)
        response = c.post(url, {'email':'testuserid@gmail.com', 'password':'test', 'terms_of_use':True}, follow=True)
        self.assertEquals([('http://testserver/profile', 302)], response.redirect_chain)

        # verify user was created
        user = authenticate(username='testuserid@gmail.com', password='test')
        self.assertTrue(user.is_active)
        self.assertEquals('testuserid@gmail.com', user.email)
        self.assertEquals('free', user.get_profile().account_level)
        self.assertTrue(len(user.get_profile().api_key)>30)

        #now simulate a payment
        response = c.get(response.redirect_chain[0][0])
        self.assertEquals('initialpayment.html', response.template[0].name)
        upgrade = response.context['upgrade']
        self.assertEquals('testuserid@gmail.com', upgrade['form']['custom'].value())

        response = c.get('/order/return', {'tx':'jq2ekfhk', 'st':'Completed'})
        self.assertEquals('orderreturn.html', response.template[0].name)
        user = authenticate(username='testuserid@gmail.com', password='test')
        self.assertTrue(response.content.find('jq2ekfhk') > 0)



    def test_duplicate_userid(self):
        url = '/register'
        c = Client()
        response = c.post(url, {'email':'testuserid@gmail.com', 'password':'test', 'terms_of_use':True})
        self.assertEquals(302, response.status_code)
        response = c.post(url, {'email':'testuserid@gmail.com', 'password':'test', 'terms_of_use':True})
        self.assertEquals('registration/register.html', response.template[0].name)
        self.assertTrue(response.content.find('Username already in use.') > 0)


class AddLibraryAccount(TestCase):
    fixtures = ['libraries']

    def setUp(self):
        self.user = librarybot.tests.create_user('scott', 'test')
        librarybot.tests.create_patron(self.user, 3, '12345', '4321', 'Scott P')

    def test_add_and_delete_account(self):
        # add account
        url = '/libraryaccount/1/add'
        c = Client()
        c.login(username='scott', password='test')
        response = c.get(url)
        self.assertEquals('libraryaccount.html', response.template[0].name)
        response = c.post(url, {'name':'Scott P', 'patronid':'12345', 'pin':'4321'}, follow=True)
        redirect_url = response.redirect_chain[0]
        self.assertEquals('http://testserver' + url, redirect_url[0])
        patrons = response.context['patrons']
        self.assertEquals(2, len(patrons))
        patron_added = [p for p in patrons if p.patronid=='12345'][0]
        self.assertEquals('Scott P', patron_added.name)
        self.assertEquals('4321', patron_added.pin)
        self.assertEquals('scott', patron_added.user.username)

        # delete account
        response = c.post('/libraryaccount/delete', {'patronid': '12345', 'return':url}, follow=True)
        redirect_url = response.redirect_chain[0]
        self.assertEquals('http://testserver' + url, redirect_url[0])
        patrons = response.context['patrons']
        self.assertEquals(1, len(patrons))



def suite():
    return unittest.TestSuite((
        unittest.makeSuite(Register,'test'),
        unittest.makeSuite(AddLibraryAccount, 'test')
    ))

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

