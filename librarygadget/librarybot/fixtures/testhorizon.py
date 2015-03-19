import unittest
from librarybot import horizon
import datetime
from librarybot import util
from BeautifulSoup import BeautifulSoup

class TestCheckedOut(unittest.TestCase):

    def testdesmoines(self):
        print "*** Des Moines ***"
        f = open("librarybot/fixtures/horizon/desmoines.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["Detours"]
        self.assertEquals("Detours", item.title)
        self.assertEquals("Crow, Sheryl", item.author)
        self.assertEquals(1, item.timesRenewed)
        self.assertEquals("11/05/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testnewyork(self):
        print "*** New York ***"
        f = open("librarybot/fixtures/horizon/ny.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["The killer's wife"]
        self.assertEquals("The killer's wife", item.title)
        self.assertEquals("Floyd, Bill", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("11/15/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testseattle(self):
        print "*** Seattle ***"
        f = open("librarybot/fixtures/horizon/seattle.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["Great expectations"]
        self.assertEquals("Great expectations", item.title)
        self.assertEquals("Dickens, Charles", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("11/05/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testseattle2(self):
        print "*** Seattle 2 ***"
        f = open("librarybot/fixtures/horizon/seattle2.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["Cars that think"]
        self.assertEquals("Cars that think", item.title)
        self.assertEquals("Alda, Alan", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("11/21/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testseattle3(self):
        f = open("librarybot/fixtures/horizon/seattle3.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["The Gutenberg elegies : the fate of reading in an electronic culture"]
        self.assertEquals("The Gutenberg elegies : the fate of reading in an electronic culture", item.title)
        self.assertEquals("Birkerts, Sven", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("07/03/2009", item.dueDate.strftime("%m/%d/%Y"))

    def testseattle4(self):
        f = open("librarybot/fixtures/horizon/seattle4.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["Horse show champ"]
        self.assertEquals("Horse show champ", item.title)
        self.assertEquals("Parker, Jessie", item.author)
        self.assertEquals(0, item.timesRenewed)
        self.assertEquals("07/07/2009", item.dueDate.strftime("%m/%d/%Y"))
        self.assertEquals(None, item.renewitemkeys)

    def testvancouver(self):
        print "*** Vancouver ***"
        f = open("librarybot/fixtures/horizon/vancouver.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["Life in the French country house"]
        self.assertEquals("Life in the French country house", item.title)
        self.assertEquals("Girouard, Mark", item.author)
        self.assertEquals(1, item.timesRenewed)
        self.assertEquals("11/24/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testmadison(self):
        print "*** Madison ***"
        f = open("librarybot/fixtures/horizon/madison.html", "r")
        html = f.read()
        page = horizon.ItemsOutPage(None, html)
        item =  page.itemsOut["Cupcake"]
        self.assertEquals("Cupcake", item.title)
        self.assertEquals("Cohn, Rachel", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("01/07/2009", item.dueDate.strftime("%m/%d/%Y"))

# hennepin is really customized and I don't want to code for it
#	def testhennepin(self):
#		f = open("tests/djangolibrarybot.librarybot.librarybot/fixtures/horizon/hennepin.html", "r")
#		html = f.read()
#		page = horizon.ItemsOutPage(None, html)
#		item =  page.itemsOut["The golden retriever"]
#		self.assertEquals("The golden retriever", item.title)
#		self.assertEquals("Adamson, Eve", item.author)
#		self.assertEquals(None, item.timesRenewed)
#		self.assertEquals("11/28/2008", item.dueDate.strftime("%m/%d/%Y"))	

class TestAccountOverview(unittest.TestCase):

    def testhennepinaccountoverview(self):
        print "*** Hennepin ***"
        f = open("librarybot/fixtures/horizon/hennepinaccountoverview.html", "r")
        html = f.read()
        page = horizon.AccountOverviewPage(None, html)
        self.assertEquals("/ipac20/ipac.jsp?session=1226T14652NN3.52506&profile=elibrary&menu=account&submenu=itemsout&ts=1226814683386&sortby=duedate", page.itemsOutUrl())





def suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestCheckedOut,'test'),
        unittest.makeSuite(TestAccountOverview, 'test')
    ))


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
