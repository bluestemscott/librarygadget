import unittest
from librarybot import koha
import librarybot.tests

class TestCheckedOut(unittest.TestCase):
    def testmadison(self):
        f = open("librarybot/fixtures/koha/madison-itemsout.htm", "r")
        html = f.read()
        page = koha.ItemsOutPage(librarybot.tests.MockHttp(), html)
        item =  page.itemsOut["All the things I love about you"]
        self.assertEquals("All the things I love about you", item.title)
        self.assertEquals("Pham, LeUyen", item.author)
        #self.assertEquals(0, item.timesRenewed)
        self.assertEquals("10/25/2011", item.dueDate.strftime("%m/%d/%Y"))
        self.assertTrue(len(item.renew_url) > 0)

    def testmadison_no_title(self):
        f = open("librarybot/fixtures/koha/madison-itemsout.htm", "r")
        html = f.read()
        page = koha.ItemsOutPage(librarybot.tests.MockHttp(), html)
        item =  page.itemsOut["Bob the Builder"]
        self.assertEquals("Bob the Builder", item.title)
        self.assertEquals('', item.author)
        #self.assertEquals(0, item.timesRenewed)
        self.assertEquals("10/04/2011", item.dueDate.strftime("%m/%d/%Y"))
        self.assertTrue(item.renewable)
        self.assertTrue(len(item.renew_url) > 0)

    def test_madison_not_renewable(self):
        f = open("librarybot/fixtures/koha/madison-norenewalsleft.htm", "r")
        html = f.read()
        page = koha.ItemsOutPage(librarybot.tests.MockHttp(), html)
        item =  page.itemsOut["Where the wild things are"]
        self.assertFalse(item.renewable)
        self.assertEquals(None, item.renew_url)

class TestLogin(unittest.TestCase):
    def testmadison(self):
        f = open("librarybot/fixtures/koha/madison-login.htm", "r")
        html = f.read()
        page = koha.LoginPage(None, html)
        action, data = page.createPost("myuser", "mypassword")



def suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLogin,'test'),
        unittest.makeSuite(TestCheckedOut, 'test')
    ))


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
    	