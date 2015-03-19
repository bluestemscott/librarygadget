import string
from xml.sax import saxutils
import logging
import sys 
import datetime
import time
import cookielib
import urlparse
import re
import htmlentitydefs
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, Comment


try:
    from google.appengine.api import urlfetch
except ImportError:
    import urllib2

__author__ = "Scott Peterson"
__version__ = "1.0"
__date__ = "$Date: 2005/07/16 00:14:20 $"
__copyright__ = "Copyright (c) 2005 Scott Peterson"

class LoginException(Exception):
    pass

class NavStateException(Exception):
    pass

def check_login_error(html):
    errors = ('Access Control Failure Page',
                'login has failed',
                'the information you submitted was invalid',
                'Login failed', 'Login Failed',
                'Invalid login',
                'Your login attempt was unsuccessful',
                'Access denied',
                'unable to validate your Library Card and PIN',
                'unable to log you on',
                'login is not successful',
                'Login problem',
                'Your login information was incorrect')
    for error in errors:
        if html.find(error) != -1:
            logging.debug("found a login error message on the page: %s" % (error))
            raise LoginException('Library login failed')



def stripNonAscii(str):
    return "".join([x for x in str if ord(x) < 128])

def toDatetime(stringDate):
    try:
        epochSeconds = time.mktime(time.strptime(stringDate, "%m/%d/%Y"))
        return datetime.date.fromtimestamp(epochSeconds)
    except ValueError:  #thrown if it's not mm/dd/yyyy format
        pass

    try:
        epochSeconds = time.mktime(time.strptime(stringDate, "%a, %b, %d, %Y"))
        return datetime.date.fromtimestamp(epochSeconds)
    except ValueError:
        pass

    try:
        epochSeconds = time.mktime(time.strptime(stringDate, "%m-%d-%y"))
        return datetime.date.fromtimestamp(epochSeconds)
    except ValueError:
        pass

    return None

def inner_text(soup):
    text = ''
    for child in soup:
        if isinstance(child, NavigableString) and not isinstance(child, Comment):
            text += child.strip()
    return text

def findlink(html, linktext):
    soup = BeautifulSoup(html)
    links = soup.findAll('a')
    for link in links:
        if link.string != None and re.search("\A\s*" + linktext + "\s*\Z", link.string) != None:
            url = link['href']
            url = url.replace('&amp;', '&')
            return url
    return None

def findlink_in_list(html, linklist):
    for text in linklist:
        url = findlink(html, text)
        if url != None:
            return url
    return None

def today():
    return datetime.date.today()

def yesterday():
    return today() - datetime.timedelta(days=1)

##

# http://effbot.org/zone/re-sub.htm#unescape-html
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def makePostData(form, input_matcher={'type':('hidden','submit',"image")}):
    fields = form.findAll('input', input_matcher)
    params = {}
    # Take care of the hidden fields
    for field in fields:
        try:
            params[field['name']] = field['value']
        except KeyError:  # thrown by BeautifulSoup when a field has value=""
            if params.has_key('name'):
                params[field['name']] = ''
    return params

def urlencode(params):
    return urllib.urlencode(dict([k.encode('utf-8'), v.encode('utf-8')] for k, v in params.items()))

class HttpConversation():
    def __init__(self, url):
        self.origurl = url
        self.lasturl = url
        self.history = []
        cookieJar = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        urllib2.install_opener(opener)

    def log_history(self, logger, full_trace=False):
        if full_trace:
            for reqResponse in self.history:
                logger("url=" + reqResponse["url"])
                logger(reqResponse["html"])
        else:
            reqResponse = self.history[len(self.history)-1]
            logger("url=" + reqResponse["url"])
            logger(reqResponse["html"])

    def post(self, url, data, headers={}):
        html = None
        if url[0] == '/' or url[0:4] == 'http':
            url = urlparse.urljoin(self.origurl, url)
        else:
            url = urlparse.urljoin(self.lasturl, url)
        self.lasturl = url
        #logging.warning("url=%s; data=%s" % (url, data))
        # sending a fake user agent because some ILS's go to a mobile view if no User-agent is sent. This breaks the parser
        req = urllib2.Request(url, data, headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/535.1'})
        html = urllib2.urlopen(req).read()
        self.history.append({"url":url, "html":html})
        return html

    def get(self, url, data='', headers={}):
        html = None
        if url[0] == '/' or url[0:4] == 'http':
            url = urlparse.urljoin(self.origurl, url)
        else:
            url = urlparse.urljoin(self.lasturl, url)
        self.lasturl = url
        req = urllib2.Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/535.1'})
        html = urllib2.urlopen(req).read()
        self.history.append({"url":url, "html":html})
        return html






