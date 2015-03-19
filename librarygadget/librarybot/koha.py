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
        forms = self.soup.find('input', {'name': ('userid')})
        return forms != None

    def createPost(self, username, password):
        form = self.soup.find("form", {"name" : "auth"})
        inputid = self.soup.find('input', {'name':('userid')})
        useridParam = inputid['name']
        inputpin = self.soup.find('input', {'name': ('password')})
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

    # Renewal link is replaced by "Not renewable" text if no renewals are allowed
    def parse_renew(self, td, item):
        renew_link = td.find('a')
        if renew_link is not None:
            item.renewable = True
            item.renew_url = renew_link['href']
        else:
            item.renewable = False
        return item

    def parse_title(self, td, item):
        link = td.find('a')
        title = util.unescape(link.text.strip(' :/.'))
        item.title = util.stripNonAscii(title)
        span = td.find('span')
        if span is not None and span.text is not None:
            item.author = span.text.strip(' :/.')
        return item

    def parse_due_date(self, td, item):
        item.dueDate = util.toDatetime(td.string.strip())
        return item

    def skip_column(self, td, item):
        return item

    def build_col_parsers(self, row):
        col_parsers = []
        tds = row.findAll('th')
        for td in tds:
            if td.find(text=re.compile("Title")) is not None:
                col_parsers.append(self.parse_title)
                continue
            if td.find(text=re.compile("Due")) is not None:
                col_parsers.append(self.parse_due_date)
                continue
            if td.find(text=re.compile("Renew")) is not None:
                col_parsers.append(self.parse_renew)
                continue
            col_parsers.append(self.skip_column)
        return col_parsers

    def parse(self):
        table = self.soup.find('table', {'id':'checkoutst'})
        rows = table.findAll('tr')
        col_parsers = self.build_col_parsers(rows[0])
        for row in rows[1:]:
            item = models.Item()
            tds = row.findAll('td')
            colno = 0
            for td in tds:
                item = col_parsers[colno](td, item)
                colno = colno+1
            self.itemsOut[item.title] = item

            #print item.title + '->' + str(item.dueDate)

    # koha renewals happen one click at a time. There's no way to selectively
    # renew multiple titles at once
    def renew(self, titles):
        renewals = self.itemsOut
        items_out_page = self
        for title in titles:
            if items_out_page.itemsOut.has_key(title) == False:
                continue
            item = items_out_page.itemsOut[title]
            if not item.renewable:
                item.renewed = False
                item.renewalError = "Not renewable"
                renewals[item.title] = item
                continue

            html = self.http.get(item.renew_url)
            items_out_page = ItemsOutPage(items_out_page.http, html)
            item = items_out_page.itemsOut[title] # get updated due date, etc
            item.renewed = True
            renewals[item.title] = item

        return renewals


class LibraryBot:
    def __init__(self, url, userid, password, name=""):
        self.http = util.HttpConversation(url)
        html = None
        html = self.http.get(url)
        loginPage = LoginPage(self.http, html)
        html = loginPage.login(userid, password)
        #logging.debug(html)
        self.itemsOutPage = ItemsOutPage(self.http, html)
        self.error = None

    def itemsOut(self):
        return self.itemsOutPage.itemsOut

    def renew(self, titles):
        return self.itemsOutPage.renew(titles)




