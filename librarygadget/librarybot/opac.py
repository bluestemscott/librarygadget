import logging
import urllib
import string
import sys 
import re
import datetime
import traceback
import time
import util
import models
import BeautifulSoup
from BeautifulSoup import Comment



__author__ = "Scott Peterson"
__version__ = "1.0"
__date__ = "$Date: 2005/07/16 00:14:20 $"
__copyright__ = "Copyright (c) 2005 Scott Peterson"


class LoginPage:
    def __init__(self, http, html):
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.html = html
        self.http = http

    def isLoginPage(self):
        forms = self.soup.find('form', {'name': ('accessform','loginWN','loginform','login2')})
        return forms != None


    def createPost(self, username, password):
        inputids = self.soup.findAll('input', {'name':('user_id', 'userid')})
        form = None
        useridParam = None
        for inputid in inputids:
            useridParam = inputid['name']
            form = inputid.findPrevious("form")
        if useridParam == None:
            raise util.NavStateException("unable to find login form, html=" + self.html)

        inputpin = form.find('input', {'name': ('password','pin')})
        if inputpin == None:
            raise util.NavStateException("unable to find login form, html=" + self.html)
        passwordParam = inputpin['name']

        logging.debug("form name=%s, useridParam=%s, passwordParam=%s" % (form["name"], useridParam, passwordParam))

        action = form['action']
        params = util.makePostData(form)
        # Fill the visible fields
        params[useridParam] = username
        params[passwordParam] = password
        data = util.urlencode(params)

        return action,data

    def login(self, username, password):
        if not self.isLoginPage():
            raise util.NavStateException("not a login page")
        action, data = self.createPost(username, password)
        #print data
        html = self.http.post(action, data, {'Content-Type': 'application/x-www-form-urlencoded'})
        #don't check this for opac... some libraries (eg, Kirkendall) embed hidden login forms on the account page
        #newPage = LoginPage(self.http, html)
        #if newPage.isLoginPage():
        #	logging.debug("found another login page after login attempt")
        #	raise util.LoginException("Library login failed")
        util.check_login_error(html)
        return html

class RenewalResultPage:
    def __init__(self, http, html):
        self.http = http
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.renewalItems = {}
        try:
            self.parse()
        except Exception, e:
            logging.error("error parsing renewal result page")
            http.log_history(logging.error)
            raise

    def parse(self):
        #print self.soup.prettify()
        dds = self.soup.findAll('dd')

        for dd in dds:
            item = models.Item()

            reasonSoup = dd.findPrevious('strong')
            print reasonSoup.prettify()
            reason = util.inner_text(reasonSoup)
            print "reason=" + reason
            if reason == 'Item renewed':
                item.renewed = True
                item.renewalError = None
            else:
                item.renewed = False
                item.renewalError = reason

            title = dd.contents[0].strip()
            title = util.unescape(title)
            title = util.stripNonAscii(title)
            self.renewalItems[title] = item



class RenewalPage:
    def __init__(self, http, html):
        self.http = http
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.renewalitems = {}
        self.form = None
        try:
            self.parse()
        except Exception, e:
            logging.error("renewal parse error on html")
            http.log_history(logging.error)
            raise

    def parse(self):
        self.form = self.soup.find('form', {'name' : 'renewitems'})
        checkboxes = self.form.findAll('input', {'type' : 'checkbox'})
        for checkbox in checkboxes:
            item = models.Item()
            item.renewitemkey = checkbox['name']

            title_label = checkbox.findNext('td').label
            title = title_label.contents[2].strip()
            title = util.unescape(title)
            item.title = util.stripNonAscii(title)

            self.renewalitems[item.title] = item

    def makeRenewalPost(self, titles):
        params = {}
        params = util.makePostData(self.form)
        params['selection_type'] = 'selected'
        data = util.urlencode(params)

        renewals = [] #keep track of items we actually tried to renew
        for title in titles:
            #print title
            if self.renewalitems.has_key(title) == False:
                continue
            renewals.append(title)
            renewalParam = {}
            item = self.renewalitems[title]
            renewalParam[item.renewitemkey] = 'on'
            data += "&" + util.urlencode(renewalParam)
        return self.form['action'], data

    def renew(self, titles):
        action, data = self.makeRenewalPost(titles)
        html = self.http.post(action, data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        #print html
        return html


class ItemsOutPage:
    def __init__(self, http, html):
        self.http = http
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.itemsOut = {}
        try:
            # two different styles of pages
            self.parse()
            if len(self.itemsOut.values()) == 0:
                self.parse_itemlisting_style()
        except Exception, e:
            logging.error("items out parse error on html")
            http.log_history(logging.error)
            raise

    #finds the content inside opac tag structures
    #  <td class="defaultstyle" align="left">         <!-- Title --><b>            The good night [videorecording]</b>        </td>
    #  <td class="defaultstyle" align="left">         <!-- Title -->           The good night [videorecording]       </td>
    def findcontent(self, td):
        for content in td:
            if isinstance(content, BeautifulSoup.Comment):
                continue
            if isinstance(content, BeautifulSoup.Tag):
                return content.string.strip()
            if len(content.strip()) > 0:
                return content.strip()

        return ''


    def parse_itemlisting_style(self):
        item_tds = self.soup.findAll('td', {'class' : ('itemlisting', 'itemlisting2')})
        for td in item_tds:
            tr = td.findPrevious('tr')
            item = models.Item()

            marker = tr.find(text=re.compile("Print the title"))
            title = marker.nextSibling.strip()
            title = util.unescape(title)
            item.title = util.stripNonAscii(title)

            marker = tr.find(text=re.compile("Print the author"))
            if marker is None or marker.nextSibling is None:
                author = ''
            else:
                author = marker.nextSibling.strip().strip('.')
            L = author.split(',')
            author = ','.join(L[0:2])
            author = util.unescape(author)
            item.author = util.stripNonAscii(author)

            marker = tr.find(text=re.compile("Print the date due"))
            #<td>Due <!--Print the date due--> <strong>12/10/2011,....
            dueDate = marker.parent.find('strong').string.strip()
            dueDate = dueDate.split(',')[0] #strip time
            item.dueDate = util.toDatetime(dueDate)
            self.itemsOut[item.title] = item
        print self.itemsOut

    def parse(self):
        duecomments = self.soup.findAll(text=re.compile("Due Date"))

        for comment in duecomments:
            tr = comment.findPrevious('tr')
            item = models.Item()

            marker = tr.find(text=re.compile("Title"))
            if marker is None:
                marker = tr.find(text=re.compile("Print the title"))
            title = self.findcontent(marker.parent)
            title = util.unescape(title)
            item.title = util.stripNonAscii(title)

            marker = tr.find(text=re.compile("Author"))
            author = self.findcontent(marker.parent)
            L = author.split(',')
            author = ','.join(L[0:2])
            author = util.unescape(author)
            item.author = util.stripNonAscii(author)

            marker = tr.find(text=re.compile("Due Date"))
            dueDate = self.findcontent(marker.parent)
            dueDate = dueDate.split(',')[0] #strip time
            item.dueDate = util.toDatetime(dueDate)
            self.itemsOut[item.title] = item

class LibraryBot:
    def __init__(self, url, userid, password, name=""):
        self.url = url
        self.userid = userid
        self.password = password
        self.items_link_text = ('Renew materials/manage holds',
                            'Review My Account/Renew My Materials',
                            'Renew Your Materials',
                            'Renew My Materials',
                            'Review My Account')
        self.my_account_link_text = ("My Account",
                                     "My Library Account",
                                     "My Account &amp; Renew My Materials")

        self.http = None

    def goToPage(self, linkTitles):
        try:
            self.http = util.HttpConversation(self.url)
            html = self.http.get(self.url)
            loginPage = LoginPage(self.http, html)
            if not loginPage.isLoginPage():
                return self.goToPageEmbeddedLogin(linkTitles)
            logging.info("logging in")
            html = loginPage.login(self.userid, self.password)
            url = util.findlink_in_list(html, linkTitles)
            if url == None:
                #go to main page
                logging.info("didn't find %s, going to My Account" % (linkTitles[0]))
                url = util.findlink_in_list(html, self.my_account_link_text)
                if url == None:
                    raise util.NavStateException("can't find main account link")
                html = self.http.get(url)
                url = util.findlink_in_list(html, linkTitles)
            if url == None:
                raise util.NavStateException("failed to find link titled " + linkTitles[0])
            logging.info("attempting to click " + linkTitles[0])
            return self.http.get(url)
        except util.LoginException, le:
            raise
        except Exception, e:
            logging.error("error going to page %s" % (linkTitles[0]))
            self.http.log_history(logging.error, full_trace=True)
            raise

    # handle opac sites that don't have a login form on the front page
    def goToPageEmbeddedLogin(self, linkTitles):
        try:
            self.http = util.HttpConversation(self.url)
            html = self.http.get(self.url)
            url = util.findlink_in_list(html, linkTitles)
            if url == None:
                logging.info("didn't find %s, going to My Account" % (linkTitles[0]))
                url = util.findlink_in_list(html, self.my_account_link_text)
                if url == None:
                    raise util.NavStateException("can't find main account link")
                html = self.http.get(url)
                url = util.findlink_in_list(html, linkTitles)
            if url == None:
                raise util.NavStateException("failed to find link titled " + linkTitles[0])
            logging.info("attempting to click " + linkTitles[0])
            html = self.http.get(url)
            # handle login page
            loginPage = LoginPage(self.http, html)
            if not loginPage.isLoginPage():
                logging.info("not a login page, returning page")
                return html
            logging.info("logging in and going to page " + linkTitles[0])
            html = loginPage.login(self.userid, self.password)
            return html
        except util.LoginException, le:
            raise
        except Exception, e:
            logging.error("error going to page %s" % (linkTitles[0]))
            self.http.log_history(logging.error, full_trace=True)
            raise

    def itemsOut(self):
        html = self.goToPage(self.items_link_text)
        itemsOutPage = ItemsOutPage(self.http, html)
        #print self.itemsOutPage.soup.prettify()
        return itemsOutPage.itemsOut

    def renew(self, titles):
        html = self.goToPage(self.items_link_text)
        renewalPage = RenewalPage(self.http, html)
        html = renewalPage.renew(titles)

        #print renewalPage.soup
        # this will be the list of what's checked out/renewed/etc
        renewalResults = RenewalResultPage(self.http, html)
        itemsOut = {}
        itemsOut = self.itemsOut()
        for item in itemsOut.values():
            if (renewalResults.renewalItems.has_key(item.title)):
                item.renewed = renewalResults.renewalItems[item.title].renewed
                item.renewalError = renewalResults.renewalItems[item.title].renewalError
            else:
                item.renewed = False

        return itemsOut


def main():	
    bot = LibraryBot('http://kcmo.sirsi.net/uhtbin/cgisirsi/x/0/0/1/1166/X/BLASTOFF', '1000122694036', '1234')
    #bot = LibraryBot('http://catalog.caro.lib.md.us/uhtbin/cgisirsi.exe/x/0/0/1/1166/X/BLASTOFF', '29600000270177', '81194')
    #bot = LibraryBot('http://64.107.155.140/uhtbin/cgisirsi/CCS/x/0/57/49?user_id=webserver&password=public', '21126001464054', 'Patron')
    #bot = LibraryBot('http://www.inlandlibrary.com/web2/tramp2.exe/login_when_needed/guest?server=1home&setting_key=english&screen=MyAccount.html', '21667070849121', '5249')
    #itemsOut = bot.renew(['All I want for Christmas is a real good tan [sound recording (compact disc)]'])
    itemsOut = bot.itemsOut()
    print itemsOut
    for item in itemsOut.values():
        print item.title





if __name__ == '__main__':
    main()


'''        for k,v in item.iteritems():
            if k.startswith("soup"):
                print k ,'=', v.prettify()
            else:
                print k, '=',  v
                '''
