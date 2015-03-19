import logging
import urllib
import string
import sys 
import re
import traceback
import time
import util
import models
import BeautifulSoup

__author__ = "Scott Peterson"
__version__ = "1.0"
__date__ = "$Date: 2005/07/16 00:14:20 $"
__copyright__ = "Copyright (c) 2005 Scott Peterson"


class LoginPage:
    def __init__(self, http, html):
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.http = http

    def isLoginPage(self):
        forms = self.soup.find('input', {'name': ('textboxOBarcode','textboxBarcode','textboxBarcodeUsername')})
        return forms != None

    def createPost(self, username, password):
        form = self.soup.find("form", {"name" : "formMain"})
        inputid = self.soup.find('input', {'name':('textboxOBarcode','textboxBarcode','textboxBarcodeUsername')})
        useridParam = inputid['name']
        inputpin = self.soup.find('input', {'name': ('textboxOPassword','textboxPassword')})
        passwordParam = inputpin['name']

        params = {}
        params = util.makePostData(form)
        params[useridParam] = username
        params[passwordParam] = password
        data = util.urlencode(params)
        action = form['action']
        logging.debug('action=' + action)
        logging.debug('data=' + data)
        return action, data

    def login(self, username, password):
        if not self.isLoginPage():
            raise util.NavStateException("not a login page")
        action, data = self.createPost(username, password)
        html = self.http.post(action, data, {'Content-Type': 'application/x-www-form-urlencoded'});
        newPage = LoginPage(None, html)
        if newPage.isLoginPage():
            raise util.LoginException("Library login failed")
        util.check_login_error(html)
        return html

class AccountOverviewPage:
    def __init__(self, http, html):
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.http = http
        #print self.soup.prettify()
        #logging.debug(html)

    def itemsOutUrl(self):
        link = self.soup.find('a', {'href':re.compile('itemsout.aspx')})
        #print self.soup.prettify()
        itemsOutURL = link['href']
        itemsOutURL = itemsOutURL.replace('&amp;', '&')
        return itemsOutURL

    def clickItemsOut(self):
        logging.debug(self.itemsOutUrl())
        return self.http.get(self.itemsOutUrl());

class PendingFineException(Exception):
    pass

class PendingFinePage:
    def __init__(self, http, html):
        self.http = http
        self.soup = BeautifulSoup.BeautifulSoup(html)

    def ok_form(self):
        form = self.soup.find('form', {'name':'formMain'})
        params = util.makePostData(form)
        del params['buttonCancel']
        data = util.urlencode(params)
        action = form['action']
        logging.warning("pending fine action: " + action)
        logging.warning("pending fine data: " + data)
        return action, data

    def click_ok(self):
        action, data = self.ok_form()
        html = self.http.post(action, data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        logging.warning("pending fine html: " + html)
        return html


class RenewalResultPage:		
    def __init__(self, http, html):
        self.http = http
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.renewalItems = {}
        self.pending_fine = False
        try:
            self.parse()
        except PendingFineException, pfe:
            self.pending_fine = True
        except Exception, e:
            logging.error("error parsing renewal result page")
            http.log_history(logging.error)
            raise

    def parse(self):
        # look for pending fine
        fine = self.soup.find('div', {'id':'panelVerifyCharges'})
        if fine != None:
            raise PendingFineException

        row = self.soup.find('div', {'id':'panelMessage'})
        titles = row.findAll('i')

        for title in titles:
            item = models.Item()

            reason = title.nextSibling.strip()
            if reason == 'is renewed.':
                item.renewed = True
                item.renewalError = None
            else:
                item.renewed = False
                error_ul = title.findNextSibling('ul')
                if error_ul == None:
                    item.renewalError = 'Renewal failed'
                else:
                    item.renewalError = error_ul.li.string

            titlestr = title.contents[0].strip()
            titlestr = util.unescape(titlestr)
            titlestr = util.stripNonAscii(titlestr)
            self.renewalItems[titlestr] = item




class ItemsOutPage:
    def __init__(self, http, html):
        self.http = http
        self.soup = BeautifulSoup.BeautifulSoup(html)
        #print self.soup.prettify()
        self.itemsOut = {}
        try:
            self.parse()
        except Exception, e:
            logging.error("error parsing items out page")
            http.log_history(logging.error)
            raise

    def error(self):
        errors = self.soup.findAll('a', {'class':'boldRedFont1'})
        errorText = ''
        for error in errors:
            if error.string != error.Null:
                errorText += error.string
        return errorText

    def parseRenew(self, td, item):
        renewitemkeys = td.find('input')
        item.renewitemkeys = renewitemkeys['name']
        return item


    def parseTitle(self, td, item):
        span = td.find('span')
        link = span.find('a')
        if link == None:
            title = span.contents[0].strip()
        else:
            title = link.contents[0].strip()
        title = util.unescape(title)
        item.title = util.stripNonAscii(title)
        return item

    def parseDueDate(self, td, item):
        span = td.find('span')
        item.dueDate = util.toDatetime(span.string.strip())
        return item

    def skipColumn(self, td, item):
        return item

    def setcolumnparsers(self, colheaders):
        # find offsets for each column in the table.  This accounts for some libraries that don't display times renewed, etc
        cols = []
        coltds = colheaders.findAll(['td','th'])
        for coltd in coltds:
            if coltd.find(text=re.compile("Title")) != None:
                cols.append(self.parseTitle)
                continue
            if coltd.find(text=re.compile("Due Date")) != None:
                cols.append(self.parseDueDate)
                continue
            cols.append(self.skipColumn)

        # first column assumed to be renewal checkbox
        cols[0] = self.parseRenew
        return cols

    def parse(self):
        self.form = self.soup.find('form', {'name':'formMain'})
        table = self.soup.find('table', {'id':'datagridItemsOut'})
        colparsers = None
        for row in table:
            #ignore comments, etc
            if not isinstance(row, BeautifulSoup.Tag):
                continue

            if row['class'] == 'ColumnHeader':
                colparsers = self.setcolumnparsers(row)
                continue

            item = models.Item()
            colno = 0
            for td in row:
                if not isinstance(td, BeautifulSoup.Tag):
                    continue
                # call column's parser function
                #print colparsers[colno]
                item = colparsers[colno](td, item)
                colno = colno+1
            self.itemsOut[item.title] = item

            #print item.title + ' ' + str(item.dueDate)

    def makeRenewalPost(self, titles):
        params = util.makePostData(self.form)

        renewals = [] #keep track of items we actually tried to renew
        for title in titles:
            if self.itemsOut.has_key(title) == False:
                continue
            item = self.itemsOut[title]
            if item.renewitemkeys != None:  # not all items have a renewal checkbox, currently our gadget UI doesn't ever suppress it though
                params[item.renewitemkeys] = 'checked'

        params['__EVENTTARGET'] = 'linkbuttonRenew'
        params['__EVENTARGUMENT'] = ''
        data = util.urlencode(params)
        action = self.form['action']
        #logging.warning("renew action: " + action)
        #logging.warning("renew data: " + data)
        return action, data

    def renew(self, titles):
        action, data = self.makeRenewalPost(titles)
        return self.http.post(action, data, headers={'Content-Type': 'application/x-www-form-urlencoded'})


class LibraryBot:
    def __init__(self, url, userid, password, name=""):
        self.http = util.HttpConversation(url)
        html = None
        html = self.http.get(url)
        loginPage = LoginPage(self.http, html)
        html = loginPage.login(userid, password)
        #logging.debug(html)
        self.accountOverviewPage = AccountOverviewPage(self.http, html)
        self.itemsOutPage = None
        self.error = None

    def itemsOut(self):
        if self.itemsOutPage == None:
            html = self.accountOverviewPage.clickItemsOut()
            #logging.debug(html)
            self.itemsOutPage = ItemsOutPage(self.http, html)
        return self.itemsOutPage.itemsOut

    def renew(self, titles):
        if self.itemsOutPage == None:
            html = self.accountOverviewPage.clickItemsOut()
            self.itemsOutPage = ItemsOutPage(self.http, html)
        html = self.itemsOutPage.renew(titles)

        renewalResults = RenewalResultPage(self.http, html)
        if renewalResults.pending_fine == True:
            pending_fine_page = PendingFinePage(self.http, html)
            html = pending_fine_page.click_ok()
            renewalResults = RenewalResultPage(self.http, html)

        for item in self.itemsOutPage.itemsOut.values():
            for renewedTitle in renewalResults.renewalItems.keys():
                if (item.title.find(renewedTitle) != -1):
                    item.renewed = renewalResults.renewalItems[renewedTitle].renewed
                    item.renewalError = renewalResults.renewalItems[renewedTitle].renewalError

        return self.itemsOutPage.itemsOut




def main():	
    bot = LibraryBot('https://libpac.leegov.com/polaris/logon.aspx?src=https%3a%2f%2flibpac.leegov.com%2fpolaris%2fpatronaccount%2fdefault.aspx%3fctx%3d1.1033.0.0.1&ctx=1.1033.0.0.1', '23069010202164', '9216')
    itemsOut = bot.itemsOut()
    if itemsOut == None:
        print 'itemsout failed: ', bot.error
    for item in itemsOut.values():
        print item.title




if __name__ == '__main__':
    main()

