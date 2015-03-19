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
from BeautifulSoup import BeautifulSoup



__author__ = "Scott Peterson"
__version__ = "1.0"
__date__ = "$Date: 2005/07/16 00:14:20 $"
__copyright__ = "Copyright (c) 2005 Scott Peterson"


class LoginPage:
	def __init__(self, http, html):
		self.soup = BeautifulSoup(html)
		self.http = http
		
	def login(self, username, password):
		form = self.soup.form
		action = form['action']
		params = util.makePostData(form)
		# Fill the visible fields
		params['userid'] = username
		params['pin'] = password
		data = urllib.urlencode(params)
		html = self.http.post(action, data, {'Content-Type': 'application/x-www-form-urlencoded'});
		return html		

class IntermediateLoginPage:
	def __init__(self, http, html):
		self.soup = BeautifulSoup(html)
		self.html = html
		self.http = http
		#print self.soup.prettify()
		
	def login(self):
		form = self.soup.form
		action = form['action']
		params = util.makePostData(form)
		data = urllib.urlencode(params)
		html = self.http.post(action, data, {'Content-Type': 'application/x-www-form-urlencoded'});
		util.check_login_error(html)
		return html		
		

class ItemsOutPage:
	def __init__(self, http, html):
		self.http = http
		self.soup = BeautifulSoup(html)
		#print self.soup.prettify()
		self.itemsOut = {}
		self.parse()
		

	def error(self):
		errors = self.soup.fetch('a', {'class':'boldRedFont1'})
		errorText = ''
		for error in errors:
			if error.string != error.Null:
				errorText += error.string
		return errorText


	def parse(self):
		self.form = self.soup.find("form", {"name" : "hasnow"})
		row = self.soup.find('input', {'name' : 'HASNOW'})
		if row == None:
			return
		
		table = row.findPrevious('table')
		#print table.__class__.__name__

		#print table.prettify()
		rows = table.findAll('tr')
		#print len(rows)
		for itemrow in rows:
			#print row.__class__.__name__

			#print row.prettify()
			# ignore the header row -- we know it's a header if there isn't a renewal checkbox next to it
			if itemrow.find('input', {'name':'HASNOW'}) == row.Null:
				continue
			item = models.Item()
			#print row.prettify()
			renewitemkeys = itemrow.find('input', {'name':'HASNOW'})
			
			divs = itemrow.findAll('div', {'id' : 'globaltext'})
			#print len(divs)
			title = divs[0].string.strip()
			title = util.unescape(title)
			item.title = util.stripNonAscii(title)
			#print title
			dueDate = divs[4].string.strip()
			dueDate = dueDate.split(',')[0] #strip time
			item.dueDate = util.toDatetime(dueDate)
			self.itemsOut[item.title] = item



	def renew(self, titles):
		params = {}
		params = util.makePostData(self.form)
		data = urllib.urlencode(params)
		
		renewals = [] #keep track of items we actually tried to renew
		for title in titles:
			if self.itemsOut.has_key(title) == False:
				continue
			renewals.append(title)
			renewalParam = {}
			item = self.itemsOut[title]
			renewalParam['renewitemkeys'] = item.renewitemkeys				
			data += "&" + urllib.urlencode(renewalParam)
		
		action = self.form['action']
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
		intermediateLoginPage = IntermediateLoginPage(self.http, loginPage.login(userid, password))
		self.itemsOutPage = ItemsOutPage(self.http, intermediateLoginPage.login())
		self.error = None

	def itemsOut(self):
		return self.itemsOutPage.itemsOut

	def renew(self, titles):
		return self.itemsOutPage.renew(titles)


	
def main():	
	#bot = LibraryBot('http://libwww.freelibrary.org/account/login.cfm', '22222045085564', '3663') 
	bot = LibraryBot('http://web2.buffalolib.org/Web2/tramp2.exe/log_in/guest?SETTING_KEY=Central&screen=myaccount.html', '1000117370014', '8998') 
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
