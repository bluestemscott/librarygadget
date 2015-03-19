import unittest
from django.test import TestCase
import logging
import datetime

import librarybot.gmail
from librarybot.models import Item
from librarybot.models import Patron
from librarybot.models import AccessLog
from librarybot import batch


today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)

# mock functions

def items_out_mock(self, password, patron_name):
    items = []
    items.append(Item(title='Due today', dueDate=today))
    items.append(Item(title='Due yesterday', dueDate=today - datetime.timedelta(days=1)))
    items.append(Item(title='Due in 1 day', dueDate=today + datetime.timedelta(days=1)))
    items.append(Item(title='Due in 2 days', dueDate=today + datetime.timedelta(days=2)))
    items.append(Item(title='Due in 5 days', dueDate=today + datetime.timedelta(days=5)))
    return items

def renew_failure(self, pin, name, titles):
    items = items_out_mock(self, pin, name)
    items = [item for item in items if item.title in titles]
    for item in items:
        item.renewed = False
        item.renewalError = 'Renewal failed'
        item.timesRenewed = 2
    return items

def renew_success(self, pin, name, titles):
    items = items_out_mock(self, pin, name)
    items = [item for item in items if item.title in titles]
    for item in items:
        item.renewed = True
        item.timesRenewed = 2
    return items


class BatchTest(TestCase):
    fixtures = ['libraries']
    orig_items_out = Patron.items_out
    orig_renew_items = Patron.renew_items

    def setUp(self):
        self.user = librarybot.tests.create_user('scollyp@gmail.com', 'test')
        librarybot.tests.create_patron(self.user, 3, '21704005627502', '4042')

    def tearDown(self):
        Patron.items_out = self.orig_items_out
        Patron.renew_items = self.orig_renew_items

    def test_materials_renew_failure(self):
        Patron.items_out = items_out_mock
        Patron.renew_items = renew_failure
        librarybot.gmail.send_email = self.send_message_renew_failure
        patron = Patron.objects.filter(library__id=3, patronid='21704005627502')[0]
        batch.process_patron(patron, today, None)
        logs = AccessLog.objects.all()
        self.assertEqual(1, len(logs))
        self.assertEquals(0, logs[0].renewed_count)
        self.assertEquals(3, logs[0].almost_due_count)
        self.assertEqual(1, logs[0].overdue_count)

    def send_message_renew_failure(self, email, server, disconnect):
        self.assertEquals("scollyp@gmail.com", email['To'])
        self.assertEquals("1 item overdue, 3 items almost due", email['Subject'])
        self.assertEquals(-1, email.as_string().find('Due in 5 days'))

    def test_materials_renew_success(self):
        Patron.items_out = items_out_mock
        Patron.renew_items = renew_success
        librarybot.gmail.send_email = self.send_message_renew_success
        patron = Patron.objects.filter(library__id=3, patronid='21704005627502')[0]
        batch.process_patron(patron, today, None)
        logs = AccessLog.objects.all()
        self.assertTrue(1, len(logs))
        self.assertEquals(4, logs[0].renewed_count)
        self.assertEquals(0, logs[0].almost_due_count)
        self.assertEqual(0, logs[0].overdue_count)

    def send_message_renew_success(self, email, server, disconnect):
        self.assertEquals("scollyp@gmail.com", email['To'])
        self.assertEquals("4 items auto-renewed", email['Subject'])
        self.assertEquals(-1, email.as_string().find('Due in 5 days'))

    def test_no_matching_items(self):
        items = []
        items.append(Item(title='Due in 5 days', dueDate=today + datetime.timedelta(days=5)))
        self.assertEquals(0, len(batch.find_almost_due(items, today)))



def html_email():
    item = Item()
    item.title = 'Test book'
    item.dueDate = datetime.date.today()
    item.timesRenewed = 2
    item.renewalError = 'Your renewal failed'
    renewed = []
    renewed.append(item)
    renewed.append(item)

    not_renewed= []
    not_renewed.append(item)
    not_renewed.append(item)
    msg = batch.create_message(renewed, not_renewed, datetime.date.today(), 'scollyp@gmail.com')
    librarybot.gmail.send_email(msg)

def suite():
    return unittest.TestSuite((unittest.makeSuite(BatchTest,'test')))

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

