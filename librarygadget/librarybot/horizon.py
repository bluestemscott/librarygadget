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

    def login(self, username, password):
        idinput = self.soup.find('input', {'name':'sec1'})
        form = idinput.findPrevious('form')
        action = form['action']
        params = util.makePostData(form)
        # Fill the visible fields
        params['sec1'] = username
        params['sec2'] = password
        data = util.urlencode(params)
        logging.debug(data)
        html = self.http.post(action, data, {'Content-Type': 'application/x-www-form-urlencoded'});
        util.check_login_error(html)
        logging.debug(html)
        return html

class AccountOverviewPage:
    def __init__(self, http, html):
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.http = http
        #print self.soup.prettify()

    def itemsOutUrl(self):
        link = self.soup.find('a', {'href':re.compile('submenu=itemsout')})
        #print self.soup.prettify()
        itemsOutURL = link['href']
        itemsOutURL = itemsOutURL.replace('&amp;', '&')
        return itemsOutURL

    def clickItemsOut(self):
        return self.http.get(self.itemsOutUrl());




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
            #http.log_history(logging.error)
            raise

    def error(self):
        errors = self.soup.findAll('a', {'class':'boldRedFont1'})
        errorText = ''
        for error in errors:
            if error.string != error.Null:
                errorText += error.string
        return errorText

    def parseRenew(self, td, item):
        renewitemkeys = td.find('input', {'name':'renewitemkeys'})
        if renewitemkeys != None:
            item.renewitemkeys = renewitemkeys['value']
        return item


    def parseTitle(self, td, item):
        links = td.findAll('a', {'class' : lambda(x):x!='boldRedFont1'})
        # for some reason many title links have a superfluous ' /' at the end -- remove this
        title = links[0].string.rstrip(' /')
        title = util.unescape(title)
        item.title = util.stripNonAscii(title)

        author = links[1].string
        author = author.rstrip('.')
        if author.startswith("by "):
            author = author.replace("by ", "", 1)
        # sometimes there is extraneous information after the author's name, ex: Dylan, Bob, 1941-
        L = author.split(',')
        author = ','.join(L[0:2])
        author = util.unescape(author)
        item.author = util.stripNonAscii(author)

        return item

    def parseTimesRenewed(self, td, item):
        links = td.findAll('a', {'class' : lambda(x):x!='boldRedFont1'})
        # some horizon sites leave timesrenewed column blank instead of 0
        timesRenewed = links[0].string.strip()
        timesRenewed = util.unescape(timesRenewed)
        try:
            item.timesRenewed = int(timesRenewed)
        except ValueError:
            item.timesRenewed = 0
        return item

    def parseOutDate(self, td, item):
        links = td.findAll('a', {'class' : lambda(x):x!='boldRedFont1'})
        item.outDate = util.toDatetime(links[0].string.strip())
        return item
        		
    def parseDueDate(self, td, item):
        links = td.findAll('a', {'class' : lambda(x):x!='boldRedFont1'})
        item.dueDate = util.toDatetime(links[0].string.strip())
        return item

    def skipColumn(self, td, item):
        return item

    def setcolumnparsers(self, colheaders):
        # find offsets for each column in the table.  This accounts for some libraries that don't display times renewed, etc
        cols = []
        coltds = colheaders.findAll('td')
        for coltd in coltds:
            if coltd.find('a', {'href':re.compile('title')}) != None:
                cols.append(self.parseTitle)
                continue
            if coltd.find('a', {'href':re.compile('renewals')}) != None:
                cols.append(self.parseTimesRenewed)
                continue
            if coltd.find('a', {'href':re.compile('duedate')}) != None:
                cols.append(self.parseDueDate)
                continue
            if coltd.find('a', {'href':re.compile('ckodate')}) != None:
                cols.append(self.parseOutDate)
                continue
            if coltd.find('input', {'name':'renewall'}) != None:
                cols.append(self.parseRenew)
                continue

            cols.append(self.skipColumn)

        return cols

    def parse(self):
        self.form = self.soup.find('form')

        # find the table of items, use the "renewall" checkbox as a marker
        renewall = self.soup.find('input', {'name':'renewall'})
        if renewall == None:
            # since "renewall" checkbox isn't there, there must not be anything checked out
            return

        table = renewall.findParent('table', {})
        colparsers = None
        # itemsOut is a dictionary of items, keyed by title
        # each item is also a dictionary
        # therefore itemsOut is a dictionary of dictionaries (for when you're too lazy to model)
        for row in table:
            #ignore comments, etc
            if not isinstance(row, BeautifulSoup.Tag):
                continue

            #first row in table (the one with the renewall button) is the column headings
            if row.find('input', {'name':'renewall'}) != row.Null:
                colparsers = self.setcolumnparsers(row)
                continue

            item = models.Item()

            # get renewal error if any
            errors = row.findAll('a', {'class':'boldRedFont1'})
            if len(errors)==1:
                error = errors[0]
                if error != error.Null:
                    item.renewalError = error.string

            colno = 0
            for td in row:
                if not isinstance(td, BeautifulSoup.Tag):
                    continue
                # call column's parser function
                item = colparsers[colno](td, item)
                colno = colno+1
            self.itemsOut[item.title] = item

            #print item.title + ' ' + str(item.dueDate)

    def makeRenewalPost(self, titles):
        params = {}
        params = util.makePostData(self.form)
        data = util.urlencode(params)

        renewals = [] #keep track of items we actually tried to renew
        for title in titles:
            if self.itemsOut.has_key(title) == False:
                continue
            renewals.append(title)
            renewalParam = {}
            item = self.itemsOut[title]
            # see for example seattle3.htm test case - not all items have a renewal checkbox
            if item.renewitemkeys != None:
                renewalParam['renewitemkeys'] = item.renewitemkeys
            data += "&" + util.urlencode(renewalParam)

        action = self.form['action']
        return action, data

    def renew(self, titles):
        action, data = self.makeRenewalPost(titles)
        html = self.http.post(action, data, headers={'Content-Type': 'application/x-www-form-urlencoded'})

        # this will be the list of what's checked out/renewed/etc
        newItemsOutPage = ItemsOutPage(self.http, html)
        self.itemsOut = {}
        self.itemsOut = newItemsOutPage.itemsOut
        #print self.itemsOut.values()
        for currentItem in self.itemsOut.values():
            #print currentItem.title
            if (currentItem.title in titles) & (currentItem.renewalError == None):
                currentItem.renewed = True
            else:
                currentItem.renewed = False

        return self.itemsOut


class LibraryBot:
    def __init__(self, url, userid, password, name=""):
        self.http = util.HttpConversation(url)
        html = None
        html = self.http.get(url)
        #print url=' + url + ' content=' + html
        loginPage = LoginPage(self.http, html)
        self.accountOverviewPage = AccountOverviewPage(self.http, loginPage.login(userid, password))
        self.itemsOutPage = None
        self.error = None

    def itemsOut(self):
        if self.itemsOutPage == None:
            self.itemsOutPage = ItemsOutPage(self.http, self.accountOverviewPage.clickItemsOut())
        return self.itemsOutPage.itemsOut

    def renew(self, titles):
        if self.itemsOutPage == None:
            self.itemsOutPage = ItemsOutPage(self.http, self.accountOverviewPage.clickItemsOut())
        return self.itemsOutPage.renew(titles)



def main():	
    #bot = LibraryBot('http://libhip.desmoineslibrary.com/ipac20/ipac.jsp?menu=account', '21704005627502', '4042')
    #bot = LibraryBot('', '23333073030593', '2683')
    itemsOut = bot.itemsOut()
    if itemsOut == None:
        print 'itemsout failed: ', bot.error
    for item in itemsOut.values():
        print item.title




if __name__ == '__main__':
    main()

