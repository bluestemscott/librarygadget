import unittest
from librarybot import opac
from librarybot import util
import librarybot.tests


class TestOtherKC(unittest.TestCase):
    def testoverview(self):
        print '*** Kansas City overview ***'
        f = open('librarybot/fixtures/opac/kc-overview.html', 'r')
        html = f.read()
        self.assertEquals("/uhtbin/cgisirsi/fe0lySDmeH/KC-CENTRAL/206666837/30", util.findlink(html, 'Review My Account'))
        self.assertEquals("/uhtbin/cgisirsi/IFLfMAd8Ps/KC-CENTRAL/206666837/92", util.findlink(html, "Renew My Materials"))

    def testrenewalform(self):
        print '*** Kansas City renewal form ***'
        f = open('librarybot/fixtures/opac/kc-renew.html', 'r')
        html = f.read()
        page = opac.RenewalPage(None, html)
        self.assertEquals('/uhtbin/cgisirsi/xL0hhocwmz/KC-CENTRAL/232896150/93', page.form['action'])
        item = page.renewalitems['ILL-Hits']
        self.assertEquals("RENEW^46028825^ILL-CD^1^ILL-Collins,Phil^ILL-Hits^", item.renewitemkey)


class TestRenewalResult(unittest.TestCase):
    def test_kc_renewalsuccess(self):
        print '*** Kansas City renewal success result ***'
        f = open('librarybot/fixtures/opac/kc-renewresult.html', 'r')
        html = f.read()
        page = opac.RenewalResultPage(librarybot.tests.MockHttp(), html)
        self.assertEquals(True, page.renewalItems['All I want for Christmas is a real good tan [sound recording (compact disc)]'].renewed)
        self.assertEquals(None, page.renewalItems['All I want for Christmas is a real good tan [sound recording (compact disc)]'].renewalError)

    def test_kc_renewalfailedresult(self):
        print '*** Kansas City renewal failed result ***'
        f = open('librarybot/fixtures/opac/kc-renewresultfailed.html', 'r')
        html = f.read()
        page = opac.RenewalResultPage(librarybot.tests.MockHttp(), html)
        self.assertEquals(False, page.renewalItems['All I want for Christmas is a real good tan [sound recording (compact disc)]'].renewed)
        self.assertEquals('Renewal limit reached.', page.renewalItems['All I want for Christmas is a real good tan [sound recording (compact disc)]'].renewalError)

    def test_montgomery_renewal_result(self):
        print '*** Montgomery renewal result ***'
        f = open('librarybot/fixtures/opac/montgomery_renewal_result.html', 'r')
        html = f.read()
        page = opac.RenewalResultPage(librarybot.tests.MockHttp(), html)

        item = page.renewalItems['Scream for ice cream. Nancy Drew and the Clue Crew #2']
        self.assertEquals(True, item.renewed)

        item = page.renewalItems['Pony problems. Nancy Drew and the Clue Crew #3']
        self.assertEquals(False, item.renewed)
        self.assertEquals('Item has holds', item.renewalError)



class TestOverview(unittest.TestCase):
    def testsandiego(self):
        print '*** San Diego overview ***'
        f = open('librarybot/fixtures/opac/sandiego-overview.html', 'r')
        html = f.read()
        self.assertEquals("/uhtbin/cgisirsi/L9tQ7V9bMf/CENTRAL/187270091/29/1169/X/1", util.findlink(html, 'Review My Account'))
        self.assertEquals("/uhtbin/cgisirsi/L9tQ7V9bMf/CENTRAL/187270091/29/1171/X/3", util.findlink(html, "Renew My Materials"))
        self.assertEquals("/uhtbin/cgisirsi/sRHRQ8D04b/CENTRAL/187270091/1/1168/X/BLASTOFF", util.findlink_in_list(html, ("My Account", "My Account &amp; Renew My Materials")))


    def test_montgomerycounty(self):
        print '*** MCPL overview ***'
        f = open('librarybot/fixtures/opac/montgomerycounty_overview.html', 'r')
        html = f.read()
        self.assertEquals("/uhtbin/cgisirsi/CLl2qVKYiq/WHITE_OAK/69750107/92", util.findlink_in_list(html, ("Renew Your Materials",)))
        bot = opac.LibraryBot(None, None, None)
        self.assertEquals("/uhtbin/cgisirsi/CLl2qVKYiq/WHITE_OAK/69750107/92", util.findlink_in_list(html, bot.items_link_text))

    def test_urbandale(self):
        print '*** Urbandale overview ***'
        f = open('librarybot/fixtures/opac/urbandale_overview.html', 'r')
        html = f.read()
        self.assertEquals("/uhtbin/cgisirsi.exe/pSFsczLIx2/URBANDALE/6630091/29/1169/X/3", util.findlink_in_list(html, ("Renew My Materials",)))
        bot = opac.LibraryBot(None, None, None)
        self.assertEquals("/uhtbin/cgisirsi.exe/pSFsczLIx2/URBANDALE/6630091/29/1169/X/3", util.findlink_in_list(html, bot.items_link_text))


    def testkirkendall(self):
        print '*** San Diego overview ***'
        f = open('librarybot/fixtures/opac/kirkendall-account.html', 'r')
        html = f.read()
        self.assertEquals("/uhtbin/cgisirsi.exe/55yPqRW2px/x/93210050/30/BLASTOFF", util.findlink_in_list(html, ("My Account", "My Account &amp; Renew My Materials")))


class TestCheckedOut(unittest.TestCase):
    def testkansascity(self):
        print "*** Kansas City ***"
        f = open("librarybot/fixtures/opac/kc-account.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(None, html)
        item =  page.itemsOut["ILL-Hits"]
        self.assertEquals("ILL-Hits", item.title)
        self.assertEquals("ILL-Collins,Phil", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("10/21/2008", item.dueDate.strftime("%m/%d/%Y"))

    def test_urbandale(self):
        print "*** Urbandale ***"
        f = open("librarybot/fixtures/opac/urbandale_items.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(librarybot.tests.mock_http, html)
        item =  page.itemsOut["The sight"]
        self.assertEquals("The sight", item.title)
        self.assertEquals("Hunter, Erin", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("12/05/2011", item.dueDate.strftime("%m/%d/%Y"))

    def test_urbandale_again(self):
        print "*** Urbandale ***"
        f = open("librarybot/fixtures/opac/urbandale_itemsout.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(librarybot.tests.mock_http, html)
        item =  page.itemsOut["Henry and the paper route"]
        self.assertEquals("Henry and the paper route", item.title)
        self.assertEquals("Cleary, Beverly", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("12/13/2011", item.dueDate.strftime("%m/%d/%Y"))

        item =  page.itemsOut["Watch for the light : readings for Advent and Christmas"]
        self.assertEquals("Watch for the light : readings for Advent and Christmas", item.title)
        self.assertEquals('', item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("12/13/2011", item.dueDate.strftime("%m/%d/%Y"))

    def testcarolinecounty(self):
        print "*** Caroline County ***"
        f = open("librarybot/fixtures/opac/carolinecounty-account.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(None, html)
        item =  page.itemsOut["Incidents in the life of a slave girl"]
        self.assertEquals("Incidents in the life of a slave girl", item.title)
        self.assertEquals("Jacobs, Harriet A. (Harriet Ann)", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("10/21/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testzionbenton(self):
        print "*** Zion Benton ***"
        f = open("librarybot/fixtures/opac/zionbenton-account.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(None, html)
        item =  page.itemsOut["Primal threat : a novel"]
        self.assertEquals("Primal threat : a novel", item.title)
        self.assertEquals("Emerson, Earl W.", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("11/03/2008", item.dueDate.strftime("%m/%d/%Y"))

        f = open("librarybot/fixtures/opac/zionbenton2-account.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(None, html)
        item =  page.itemsOut["Adobe Photoshop elements 6"]
        self.assertEquals("Adobe Photoshop elements 6", item.title)
        self.assertEquals("", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("01/10/2009", item.dueDate.strftime("%m/%d/%Y"))

    def testenochpratt(self):
        print "*** Enoch Pratt ***"
        f = open("librarybot/fixtures/opac/enochpratt-account.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(None, html)
        item =  page.itemsOut["The good night [videorecording]"]
        self.assertEquals("The good night [videorecording]", item.title)
        self.assertEquals("Gigliotti, Donna.", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("12/28/2008", item.dueDate.strftime("%m/%d/%Y"))

    def testsandiego(self):
        f = open("librarybot/fixtures/opac/sandiego-account.html", "r")
        html = f.read()
        page = opac.ItemsOutPage(None, html)
        item =  page.itemsOut["A version of the truth"]
        self.assertEquals("A version of the truth", item.title)
        self.assertEquals("Kaufman, Jennifer.", item.author)
        self.assertEquals(None, item.timesRenewed)
        self.assertEquals("01/20/2009", item.dueDate.strftime("%m/%d/%Y"))


class TestLogin(unittest.TestCase):
    def testinland(self):
        print '*** Inland Library***'
        f = open('librarybot/fixtures/opac/inlandlibrary-login.html', 'r')
        html = f.read()
        page = opac.LoginPage(None, html)
        action,data = page.createPost('123456', '654321')
        self.assertEquals('/web2/tramp2.exe/login_when_needed/A1g92rf9.000', action)
        self.assertEquals('pin=654321&userid=123456&screen=MyAccount.html&fail_screen=LoginOTFFailed.html&server=&item=&item_source=', data)

    def testcincinatti(self):
        print '*** Cincinatti ***'
        f = open('librarybot/fixtures/opac/cincinatti-login.html', 'r')
        html = f.read()
        page = opac.LoginPage(None, html)
        action,data = page.createPost('123456', '654321')
        self.assertEquals('/uhtbin/cgisirsi/MdaMpeyyCY/MAIN/103060007/30', action)
        self.assertEquals('password=654321&user_id=123456', data)

    def testkc(self):
        print '*** Kansas City ***'
        f = open('librarybot/fixtures/opac/kc-login.html', 'r')
        html = f.read()
        page = opac.LoginPage(None, html)
        action,data = page.createPost('123456', '654321')
        self.assertEquals('/uhtbin/cgisirsi/dftvVueApG/KC-CENTRAL/0/57/49', action)
        self.assertEquals('password=654321&user_id=123456', data)


class TestMain(unittest.TestCase):
    def testschaumburg(self):
        f = open('librarybot/fixtures/opac/schaumburg-main.html', 'r')
        html = f.read()
        url = util.findlink(html, 'My Account')
        self.assertEquals('/uhtbin/cgisirsi/1o6Sc55Rfz/CENTRAL/251370023/1/1166/X/BLASTOFF', url)


def suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestOtherKC,'test'),
        unittest.makeSuite(TestCheckedOut,'test'),
        unittest.makeSuite(TestLogin, 'test'),
        unittest.makeSuite(TestMain, 'test'),
        unittest.makeSuite(TestRenewalResult, 'test'),
        unittest.makeSuite(TestOverview, 'test')
    ))


if __name__ == '__main__':
    unittest.main()
