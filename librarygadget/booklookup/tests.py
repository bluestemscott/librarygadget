import unittest
from django.test import TestCase
from django.test.client import Client
import amazon
import models
import views



class TestAmazon(TestCase):

    def assert_not_empty(self, item_result):
        self.assertTrue(item_result.itemurl != None)
        self.assertTrue(item_result.imageurl != None)
        self.assertTrue(item_result.small_image_url != None)
        self.assertTrue(item_result.medium_image_url != None)
        self.assertTrue(item_result.large_image_url != None)
        self.assertTrue(item_result.isbn != None)

    def test_lookup_item(self):
        itemresult = amazon.blended_search('Love in the Ruins', 'Percy, Walker')
        self.assertEquals('amazon', itemresult.source)
        self.assert_not_empty(itemresult)

    def test_books_search(self):
        itemresult = amazon.books_search('Love in the Ruins', None)
        self.assertEquals('amazon', itemresult.source)
        self.assert_not_empty(itemresult)

    def test_music_search(self):
        item_result = amazon.music_search('The most relaxing guitar music in the universe', '')
        self.assertEquals('amazon', item_result.source)
        self.assertTrue(item_result.itemurl != None)
        self.assertTrue(item_result.imageurl != None)
        self.assertTrue(item_result.small_image_url != None)
        self.assertTrue(item_result.medium_image_url != None)
        self.assertTrue(item_result.large_image_url != None)
        self.assertEquals(None, item_result.isbn)

    def test_item_loookup(self):
        itemresult = amazon.item_lookup('Love in the Ruins', 'Percy, Walker')
        self.assertEquals('amazon', itemresult.source)
        self.assert_not_empty(itemresult)

    def noop_test_no_image(self):
        itemresult = amazon.item_lookup('Judas and the Gospel of Jesus : have we missed the truth about Christianity?', 'Wright, N. T. (Nicholas Thomas)')
        self.assertEquals('amazon', itemresult.source)
        self.assert_not_empty(itemresult)

    def test_create_itemresult(self):
        f = open("booklookup/fixtures/amazonSample.xml", "r")
        xml = f.read()
        itemresult = amazon.create_itemresult(xml)
        self.assertEquals('http://www.amazon.com/LoveRuinsWalkerPercy/dp/0312243111%3FSubscriptionId%3D05Q8PC91S74RJABEF202%26tag%3Dlibrgadg20%26linkCode%3Dxm2%26camp%3D2025%26creative%3D165953%26creativeASIN%3D0312243111', itemresult.itemurl)
        self.assertEquals('http://ecx.imagesamazon.com/images/I/41T44X8QRYL._SL160_.jpg', itemresult.imageurl)
        self.assertEquals('0312243111', itemresult.isbn)
        self.assertEquals('amazon', itemresult.source)

    def test_view(self):
        c = Client()
        response = c.get('/booklookup/Love%20in%20the%20ruins/Walker%20Percy/amazon.json/')
        print response.content

def suite():
    return unittest.makeSuite(TestAmazon,'test')


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())


