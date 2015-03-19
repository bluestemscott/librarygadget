import unittest
from django.test import TestCase
import logging

import librarybot.gmail
from librarybot import models

class FakeIpn():
    pass

class PaypalTest(TestCase):
    fixtures = ['libraries']

    def setUp(self):
        self.user = librarybot.tests.create_user('scott_free@test.com', 'test')
        librarybot.tests.create_patron(self.user, 3, '21704005627502', '4042')

    def test_payment_success(self):
        librarybot.gmail.send_message = self.send_message_confirm
        ipn_obj = FakeIpn()
        ipn_obj.custom = 'scott_free@test.com'
        ipn_obj.invoice = '123456'
        ipn_obj.txn_id = '123456'
        models.paypal_ipn_success(ipn_obj)

    def send_message_confirm(self, email, subject, body):
        self.assertEquals("scott_free@test.com", email)
        self.assertEquals("Library Gadget payment confirmation", subject)
        self.assertTrue(body.find('Your confirmation number is 123456.') > 0)

def suite():
    return unittest.TestSuite((unittest.makeSuite(PaypalTest,'test')))

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

