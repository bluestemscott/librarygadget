import unittest
from librarybot import sirsidynix
import datetime
from librarybot import util
from BeautifulSoup import BeautifulSoup

class TestCheckedOut(unittest.TestCase):
	def testphilly(self):
		print "*** Philadelphia ***"
		f = open("librarybot/fixtures/sirsidynix/philly.html", "r")
		html = f.read()
		page = sirsidynix.ItemsOutPage(None, html)
		item =  page.itemsOut["The hunt club"]
		self.assertEquals("The hunt club", item.title)
		self.assertEquals(None, item.timesRenewed)
		self.assertEquals(None, item.author)
		self.assertEquals("09/29/2008", item.dueDate.strftime("%m/%d/%Y"))
		

		
def suite():
	return unittest.makeSuite(TestCheckedOut,'test')

		
if __name__ == '__main__':
    unittest.main()
	