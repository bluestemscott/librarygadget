from __future__ import with_statement
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




def find_checkout_form(soup):
    return soup.find('form', {'name' : lambda(x):x=='process_form_2' or x=='checkout_form'})

class LoginPage:
    def __init__(self, http, html, url):
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.http = http
        self.url = url

    def isLoginPage(self):
        return self.soup.find('input', {'name':'code'}) != None

    def makePost(self, username, password, name):
        idinput = self.soup.find('input', {'name':'code'})
        form = idinput.findPrevious('form')
        action = None
        try:
            action = form['action']
        except KeyError:
            action = self.url
        params = util.makePostData(form)
        # Fill the visible fields
        params['code'] = username
        if form.find('input', {'name':'pin'}) != None:
            logging.debug("found pin field")
            params['pin'] = password
        if form.find('input', {'name':'name'}) != None:
            logging.debug("found name field")
            params['name'] = name

        # Spring web flow params aren't inside the form since they're submitted by js
        flow_params = util.makePostData(self.soup, {'type':'hidden', 'name':('lt','_eventId')})
        params.update(flow_params)
        data = util.urlencode(params)
        return action, data

    def login(self, username, password, name):
        if not self.isLoginPage():
            raise util.NavStateException("not a login page")
        action, data = self.makePost(username, password, name)
        logging.debug("action=%s, data=%s" % (action, data))
        html = self.http.post(action, data, {'Content-Type': 'application/x-www-form-urlencoded'});
        # check to see if this is a login page
        newPage = LoginPage(None, html, None)
        if newPage.isLoginPage():
            logging.debug("found another login page")
            raise util.LoginException("Library login failed")
        # double check for a login error message
        util.check_login_error(html)
        #logging.debug(html)
        return html

class AccountOverviewPage:
    def __init__(self, http, html):
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.http = http
        #print self.soup.prettify()

    def itemsOutUrl(self):
        link = self.soup.find('a', {'href':re.compile('/items')})
        if link == self.soup.Null:
            return None
        itemsOutURL = link['href']
        itemsOutURL = itemsOutURL.replace('&amp;', '&')
        return itemsOutURL

    def clickItemsOut(self):
        url = self.itemsOutUrl()
        if url == None:
            return None
        return self.http.get(self.itemsOutUrl())

    def contains_items_out(self):
        return find_checkout_form(self.soup) is not None


class ItemsOutPage:
    def __init__(self, http, html, url):
        self.http = http
        self.url = url
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.form = find_checkout_form(self.soup)
        #print self.soup.prettify()
        self.itemsOut = {}
        try:
            self.parse()
        except Exception, e:
            logging.error("error parsing items out")
            if http is not None:
                http.log_history(logging.error)
            raise


    def parse(self):
        noentries = self.soup.find('tr', {'class':'patFuncNoEntries'})
        if noentries != None:
            self.itemsOut = {}
            return self.itemsOut

        rows = self.form.findAll('tr', {'class':'patFuncEntry'})
        for row in rows:
            #ignore comments, etc
            if not isinstance(row, BeautifulSoup.Tag):
                continue

            item = models.Item()

            # title/author link <a href="/patroninfo~S51/1443596/item&1816471"> The cleaner / Brett Battles. </a>
            # or sometimes it's not a link: /Making Marines;DVD;;;
            titletd = row.find('td', {'class' : 'patFuncTitle'})
            #print str(titletd)
            titlelink = titletd.find('a')
            if titlelink is None:
                titlestr = titletd.string
            else:
                # <a href="...">Time Magazine <span>August 2011</span></a>
                titlestr = titlelink.text
            #print titlestr
            parts = titlestr.split('/')
            #if there's nothing before the /, remove it.  We will assume what came after the / is the title
            # ie. /Making Marines;DVD;;;
            if len(parts)>1 and parts[0].strip() == '':
                del(parts[0])

            # for some reason many title links have a superfluous ' /' at the end -- remove this
            title = parts[0].strip(' /.')
            title = title.strip()
            title = util.unescape(title)
            item.title = util.stripNonAscii(title)
            #print item.title

            if len(parts) > 1:
                author = parts[1]
                author = author.strip(' .')
                if author.startswith("by "):
                    author = author.replace("by ", "", 1)
                # sometimes there is extraneous information after the author's name, ex: Dylan, Bob, 1941-
                L = author.split(',')
                author = ','.join(L[0:2])
                author = util.unescape(author)
                item.author = util.stripNonAscii(author)

            #<td align="left" class="patFuncStatus"> DUE 12-22-08 <em><b>  RENEWAL SUCCESSFUL</b><br />Now due 12-30-08</em> <span  class="patFuncRenewCount">Renewed 1 time</span>
            #<td align="left" class="patFuncStatus">DUE 11-23-08</td>
            #<td align="left" class="patFuncStatus">DUE 11-23-08 +1 HOLD</td>
            #<td align="left" class="patFuncStatus"> DUE 02-27-09ORPHAN SHELF  <span  class="patFuncRenewCount">Renewed 2 times</span></td>
            statustd = row.find('td', {'class' : 'patFuncStatus'})
            duedate = None
            if str(statustd).find("Now due") != -1:
                em = statustd.em
                duetext = em.contents[2].strip()
                duewords = duetext.split()
                duedate = duewords[2]
            else:
                duetext = statustd.contents[0].strip()
                duewords = duetext.split()
                duedate = duewords[1]
                if len(duedate) > 8:
                    duedate = duedate[0:8]
            #print duedate
            item.dueDate = util.toDatetime(duedate)
            # get renewal error if any
            errors = statustd.find('font', {'color':'red'})
            if errors != None and len(errors)==1:
                error = errors.contents[0].strip()
                if error.find("RENEWED") != -1:
                    item.renewalError = error

            #           <span class="patFuncRenewCount">Renewed 1 time</span>
            renewedspan = row.find('span', {'class' : 'patFuncRenewCount'})
            if renewedspan != row.Null:
                timesRenewed = renewedspan.string.strip()
                timesRenewed = util.unescape(timesRenewed)
                words = timesRenewed.split(' ')
                item.timesRenewed = int(words[1])
            else:
                item.timesRenewed = 0

            # renew checkbox
            renewitem = row.find('input', {'name': re.compile('renew')})
            item.renewitemkey = None
            if renewitem != None:
                item.renewitemkey = renewitem['name']
                item.renewitemvalue = renewitem['value']
            self.itemsOut[item.title] = item

            #print item.title + ' ' + str(item.dueDate)

    def makeRenewalPost(self, titles):
        params = {}
        params = util.makePostData(self.form)
        data = util.urlencode(params)

        for title in titles:
            if self.itemsOut.has_key(title) == False:
                continue
            renewalParam = {}
            item = self.itemsOut[title]
            if item.renewitemkey != None:  # not all items have a renewal checkbox, currently our gadget UI doesn't ever suppress it though
                renewalParam[item.renewitemkey] = item.renewitemvalue
                data += "&" + util.urlencode(renewalParam)

        action = None
        try:
            action = self.form['action']
        except KeyError:
            action = self.url

        return action, data

    def renew(self, titles):
        action, data = self.makeRenewalPost(titles)
        html = self.http.post(action, data, headers={'Content-Type': 'application/x-www-form-urlencoded'})

        # this will be the list of what's checked out/renewed/etc
        newItemsOutPage = ItemsOutPage(self.http, html, self.url)
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
        loginPage = LoginPage(self.http, html, url)
        logging.debug("name=%s" % (name))
        html = loginPage.login(userid, password, name)
        self.accountOverviewPage = AccountOverviewPage(self.http, html)
        self.itemsOutPage = None
        if self.accountOverviewPage.contains_items_out():
            self.itemsOutPage = ItemsOutPage(self.http, html, 'account_overview')
        self.error = None

    def itemsOut(self):
        if self.itemsOutPage == None:
            html = self.accountOverviewPage.clickItemsOut()
            if html == None:
                itemsOut = {}
                return itemsOut
            self.itemsOutPage = ItemsOutPage(self.http, html, self.accountOverviewPage.itemsOutUrl())
        return self.itemsOutPage.itemsOut

    def renew(self, titles):
        if self.itemsOutPage == None:
            html = self.accountOverviewPage.clickItemsOut()
            if html == None:
                itemsOut = {}
                return itemsOut
            self.itemsOutPage = ItemsOutPage(self.http, html, self.accountOverviewPage.itemsOutUrl())
        return self.itemsOutPage.renew(titles)



def main():	
    #bot = LibraryBot('https://sflib1.sfpl.org/patroninfo~S1', '21223024932231', '3023')
    #bot = LibraryBot('https://www.saclibrarycatalog.org/patroninfo~S51', '23029013264660', '0866')
    #bot = LibraryBot('http://waldo.library.nashville.org/patroninfo', '25192005235094', '8706')
    bot = LibraryBot('https://catalog.kcls.org/patroninfo~S1', '0032442113', '6786')
    itemsOut = bot.itemsOut()
    if itemsOut == None:
        print 'itemsout failed: ', bot.error
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
