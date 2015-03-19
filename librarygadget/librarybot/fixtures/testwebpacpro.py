import unittest
from librarybot import webpacpro
import datetime
from librarybot import util
from BeautifulSoup import BeautifulSoup

class TestOverview(unittest.TestCase):
    def testsanfran(self):
        print '*** San Francisco ***'
        f = open('librarybot/fixtures/webpacpro/sanfran-overview.html', 'r')
        html = f.read()
        page = webpacpro.AccountOverviewPage(None, html)
        self.assertEquals("/patroninfo~S1/1117287/items", page.itemsOutUrl())

    def testsacramento(self):
        print '*** Sacramento ***'
        f = open('librarybot/fixtures/webpacpro/sacramento-overview.html', 'r')
        html = f.read()
        page = webpacpro.AccountOverviewPage(None, html)
        self.assertEquals("/patroninfo~S51/1443596/items", page.itemsOutUrl())

    def testlakeland(self):
        print '*** Lakeland ***'
        f = open('librarybot/fixtures/webpacpro/lakeland-overview.html', 'r')
        html = f.read()
        page = webpacpro.AccountOverviewPage(None, html)
        self.assertEquals("/patroninfo~S1/1412789/items", page.itemsOutUrl())


class TestItemsOut(unittest.TestCase):	
    def testsanfran(self):
        print '*** San Francisco***'
        f = open('librarybot/fixtures/webpacpro/sanfran-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["To our children's children's children [sound recording]"]
        self.assertEquals("To our children's children's children [sound recording]", item.title)
        self.assertEquals("Moody Blues", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("12/07/2008", item.dueDate.strftime("%m/%d/%Y"))

        item =  page.itemsOut["Looney tunes golden collection. Vol. 4 [videorecording]"]
        self.assertEquals("Looney tunes golden collection. Vol. 4 [videorecording]", item.title)
        self.assertEquals("[Warner Bros. presents]", item.author)
        self.assertEquals(1, item.timesRenewed)
        self.assertEquals("11/23/2008", item.dueDate.strftime("%m/%d/%Y"))

        item =  page.itemsOut["Seventh sojourn [sound recording]"]
        self.assertEquals("Seventh sojourn [sound recording]", item.title)
        self.assertEquals(None, item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("12/07/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testsacramento(self):
        print '*** Sacramento***'
        f = open('librarybot/fixtures/webpacpro/sacramento-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["Exit ghost"]
        self.assertEquals("Exit ghost", item.title)
        self.assertEquals("Philip Roth", item.author)
        self.assertEquals(3, item.timesRenewed)
        self.assertEquals("11/17/2008", item.dueDate.strftime("%m/%d/%Y"))

        item =  page.itemsOut["The watchman"]
        self.assertEquals("The watchman", item.title)
        self.assertEquals("Robert Crais", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("11/20/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testsacramento2(self):
        print '*** Sacramento ***'
        f = open('librarybot/fixtures/webpacpro/sacramento-itemsout2.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["20 all-time greatest hits [sound recording]"]
        self.assertEquals("20 all-time greatest hits [sound recording]", item.title)
        self.assertEquals("James Brown", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("12/23/2008", item.dueDate.strftime("%m/%d/%Y"))


    def testlakeland(self):
        print '*** Lakeland***'
        f = open('librarybot/fixtures/webpacpro/lakeland-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["Infected : a novel"]
        self.assertEquals("Infected : a novel", item.title)
        self.assertEquals("Scott Sigler", item.author)
        self.assertEquals(1, item.timesRenewed)
        self.assertEquals("11/21/2008", item.dueDate.strftime("%m/%d/%Y"))

        item =  page.itemsOut["Promises to keep"]
        self.assertEquals("Promises to keep", item.title)
        self.assertEquals("Charles De Lint", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("12/08/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testallegheny(self):
        print '*** Allegheny***'
        f = open('librarybot/fixtures/webpacpro/allegheny-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["The war [videorecording]"]
        self.assertEquals("The war [videorecording]", item.title)
        self.assertEquals("a Ken Burns film ; a production of Florentine Films ; produced in associa", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("12/29/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testsaltlakecity(self):
        print '*** Salt Lake City library ***'
        f = open('librarybot/fixtures/webpacpro/saltlakecity-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        self.assertEquals(0, len(page.itemsOut))

    def testkingcounty(self):
        print '*** King County ***'
        f = open('librarybot/fixtures/webpacpro/king-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["Echo echo [sound recording]"]
        self.assertEquals("Echo echo [sound recording]", item.title)
        self.assertEquals("Carbon Leaf", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("12/30/2008", item.dueDate.strftime("%m/%d/%Y"))



    def testpalosverdes(self):
        print '*** Palos Verdes ***'
        f = open('librarybot/fixtures/webpacpro/palosverdes-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["It's time [sound recording]"]
        self.assertEquals("It's time [sound recording]", item.title)
        self.assertEquals("Michael Buble", item.author)
        self.assertEquals(2, item.timesRenewed)
        self.assertEquals("02/27/2009", item.dueDate.strftime("%m/%d/%Y"))

    def test_clive(self):
        print '*** Clive ***'
        f = open('librarybot/fixtures/webpacpro/clive-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["Triathlete.August 2011"]
        self.assertEquals("Triathlete.August 2011", item.title)
        self.assertEquals(None, item.author)
        self.assertEquals(1, item.timesRenewed)
        self.assertEquals("09/19/2011", item.dueDate.strftime("%m/%d/%Y"))

    def test_pls(self):
        print '*** Peninsula Library System ***'
        f = open('librarybot/fixtures/webpacpro/pls-itemsout.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["Independence day"]
        self.assertEquals("Independence day", item.title)
        self.assertEquals('Richard Ford', item.author)
        self.assertEquals(2, item.timesRenewed)
        self.assertEquals("11/09/2011", item.dueDate.strftime("%m/%d/%Y"))


class TestRenewal(unittest.TestCase):
    def testkingcounty(self):
        print '*** King County***'
        f = open('librarybot/fixtures/webpacpro/king-renewal.html', 'r')
        html = f.read()
        page = webpacpro.ItemsOutPage(None, html, None)
        item =  page.itemsOut["Dhaai akshar prem ke [videorecording]"]
        self.assertEquals("Dhaai akshar prem ke [videorecording]", item.title)
        self.assertEquals("a Raj Kanwar film ; produced and directed by, Raj Kanwar", item.author)
        self.assertEquals(1, item.timesRenewed)
        self.assertEquals("12/30/2008", item.dueDate.strftime("%m/%d/%Y"))

        item =  page.itemsOut["Chithiram pesuthadi [videorecording]"]
        self.assertEquals("Chithiram pesuthadi [videorecording]", item.title)
        self.assertEquals("director, Mysskin ; producer", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("ITEM CANNOT BE RENEWED BECAUSE THERE ARE HOLDS WAITING", item.renewalError)
        self.assertEquals("12/22/2008", item.dueDate.strftime("%m/%d/%Y"))

class TestLogin(unittest.TestCase):
    pass
    # This currently does not parse in BeautifulSoup.. maybe html5lib?
    def donottestmillenium(self):
        f = open('librarybot/fixtures/webpacpro/millenium-login.html', 'r')
        html = f.read()
        page = webpacpro.LoginPage(None, html, None)
        action, data = page.makePost('barcode', 'pin', 'name')
        print action
        print data

def suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestOverview,'test'),
        unittest.makeSuite(TestItemsOut, 'test'),
        unittest.makeSuite(TestRenewal, 'test'),
        unittest.makeSuite(TestLogin, 'test')
    ))



if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
