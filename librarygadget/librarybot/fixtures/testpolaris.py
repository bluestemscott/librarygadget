import unittest
from librarybot import polaris
import librarybot.tests

class TestCheckedOut(unittest.TestCase):
    def testleecounty(self):
        f = open("librarybot/fixtures/polaris/leecounty-itemsout.html", "r")
        html = f.read()
        page = polaris.ItemsOutPage(None, html)
        item =  page.itemsOut["Graduate admissions essays : write your way into the graduate school of your choice"]
        self.assertEquals("Graduate admissions essays : write your way into the graduate school of your choice", item.title)
        self.assertEquals(None, item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("04/07/2009", item.dueDate.strftime("%m/%d/%Y"))

    def testleecounty2(self):
        f = open("librarybot/fixtures/polaris/leecounty-itemsout2.html", "r")
        html = f.read()
        page = polaris.ItemsOutPage(None, html)
        item =  page.itemsOut["God is back : how the global revival of faith is changing the world"]
        self.assertEquals("God is back : how the global revival of faith is changing the world", item.title)
        self.assertEquals(None, item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("07/13/2009", item.dueDate.strftime("%m/%d/%Y"))


class TestAccountOverview(unittest.TestCase):
    def testleecounty(self):
        f = open("librarybot/fixtures/polaris/leecounty-accountoverview.html", "r")
        html = f.read()
        page = polaris.AccountOverviewPage(None, html)
        self.assertEquals(u"https://libpac.leegov.com/polaris/patronaccount/itemsout.aspx?ctx=1.1033.0.0.1", page.itemsOutUrl())


class TestLogin(unittest.TestCase):
    def testleecounty(self):
        f = open("librarybot/fixtures/polaris/leecounty-login.html", "r")
        html = f.read()
        page = polaris.LoginPage(None, html)
        action, data = page.createPost("myuser", "mypassword")

    def testmidcolumbia(self):
        f = open("librarybot/fixtures/polaris/midcolumbia-login.html", "r")
        html = f.read()
        page = polaris.LoginPage(None, html)
        action, data = page.createPost("myuser", "mypassword")

class TestRenewalResult(unittest.TestCase):
    def testmaricopasuccess(self):
        f = open("librarybot/fixtures/polaris/maricopa-renewalresult.html", "r")
        html = f.read()
        page = polaris.RenewalResultPage(librarybot.tests.mock_http, html)
        print page.renewalItems

        item = page.renewalItems["The remains of the dead : a"]
        self.assertTrue(item.renewed)
        self.assertEquals(None, item.renewalError)
        item = page.renewalItems["Reunion in death"]
        self.assertTrue(item.renewed)
        self.assertEquals(None, item.renewalError)

    def testpalsfine(self):
        f = open("librarybot/fixtures/polaris/pals-renewalfineresult.html", "r")
        html = f.read()
        page = polaris.RenewalResultPage(None, html)
        self.assertTrue(page.pending_fine)

    def test_pwc_renewal_result(self):
        f = open("librarybot/fixtures/polaris/pwc_renewal_result.html", "r")
        html = f.read()
        page = polaris.RenewalResultPage(librarybot.tests.mock_http, html)
        self.assertEquals(4, len(page.renewalItems))
        print page.renewalItems


def suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLogin,'test'),
        unittest.makeSuite(TestAccountOverview, 'test'),
        unittest.makeSuite(TestCheckedOut, 'test'),
        unittest.makeSuite(TestRenewalResult, 'test')
    ))


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
