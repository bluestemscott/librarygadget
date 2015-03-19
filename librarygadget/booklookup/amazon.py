import urllib
import urllib2
import datetime
import hmac
import hashlib
import base64
import logging
import re
import models

from xml.etree import ElementTree as ET
from elementtree import SimpleXMLTreeBuilder
ET.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder

awsversion = '2009-07-01'

class AmazonException(Exception):
    pass

def signed_querystring(params):
    paramlist = []
    keys = [key for key in params.keys() if params[key]!=None]
    keys.sort()
    for key in keys:
        paramlist.append(urllib.quote(key) + '=' + urllib.quote(params[key]))

    message = '\n'.join(['GET',
                        'ecs.amazonaws.com',
                        '/onca/xml',
                        '&'.join(paramlist)])
    #print message
    sig = hmac.new('', message, hashlib.sha256)
    base64_sig = base64.b64encode(sig.digest())
    paramlist.append('Signature=' + urllib.quote(base64_sig))
    querystring = '&'.join(paramlist)
    #print querystring
    return querystring

def blended_search(title, author):
    params = {}
    params['Service'] = 'AWSECommerceService'
    params['AssociateTag'] = 'librgadg-20'
    params['AWSAccessKeyId'] = ''
    params['Operation'] = 'ItemSearch'
    params['Version'] =  awsversion
    params['SearchIndex'] = 'Blended'
    params['Keywords'] = title + ' ' + author
    params['ResponseGroup'] = 'Images,ItemAttributes,Similarities'
    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)
    params['Timestamp'] = now.isoformat('T') + 'Z'
    #params['ResponseGroup'] =  . $ResponseGroup;
    url = "http://ecs.amazonaws.com/onca/xml?" + signed_querystring(params)
    req = urllib2.Request(url)
    xml = urllib2.urlopen(req).read()
    return create_itemresult(xml)


def books_search(title, author):
    params = {}
    params['Service'] = 'AWSECommerceService'
    params['AssociateTag'] = 'librgadg-20'
    params['AWSAccessKeyId'] = ''
    params['Operation'] = 'ItemSearch'
    params['Version'] =  awsversion
    params['SearchIndex'] = 'Books'
    params['Title'] = title
    params['Author'] = author
    params['ResponseGroup'] = 'Images,ItemAttributes,Similarities'
    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)
    params['Timestamp'] = now.isoformat('T') + 'Z'
    #params['ResponseGroup'] =  . $ResponseGroup;
    url = "http://ecs.amazonaws.com/onca/xml?" + signed_querystring(params)
    req = urllib2.Request(url)
    xml = urllib2.urlopen(req).read()
    return create_itemresult(xml)

def music_search(title, author):
    params = {}
    params['Service'] = 'AWSECommerceService'
    params['AssociateTag'] = 'librgadg-20'
    params['AWSAccessKeyId'] = ''
    params['Operation'] = 'ItemSearch'
    params['Version'] =  awsversion
    params['SearchIndex'] = 'Music'
    params['Keywords'] = title
    params['ResponseGroup'] = 'Images,ItemAttributes,Similarities'
    now = datetime.datetime.utcnow()
    now = now.replace(microsecond=0)
    params['Timestamp'] = now.isoformat('T') + 'Z'
    #params['ResponseGroup'] =  . $ResponseGroup;
    url = "http://ecs.amazonaws.com/onca/xml?" + signed_querystring(params)
    req = urllib2.Request(url)
    xml = urllib2.urlopen(req).read()
    return create_itemresult(xml)


def image_url(match):
    url = "/images/none.jpg"
    if match is not None:
        url = match.strip()
    return url


def create_itemresult(xml):
    logging.debug(xml)
    itemresult = models.ItemResult()
    ns = '{http://webservices.amazon.com/AWSECommerceService/'+ awsversion + '}'
    itemresult.source = 'amazon'
    root = ET.fromstring(xml)
    valid = root.findtext('.//' + ns + 'IsValid')
    if valid == None:
        logging.info('Missing IsValid in response')
        return
    if valid == 'False':
        logging.info('Amazon reported invalid request')
        return
    detailurl = root.findtext('.//' + ns + 'DetailPageURL')
    if detailurl == None:
        logging.info("Didn't find DetailPageURL in response")
        return

    itemresult.itemurl = detailurl.strip()
    itemresult.small_image_url = image_url(root.findtext('.//' + ns + 'SmallImage/' + ns + 'URL'))
    itemresult.medium_image_url = image_url(root.findtext('.//'  + ns + 'MediumImage/' + ns + 'URL'))
    itemresult.large_image_url = image_url(root.findtext('.//' + ns + 'LargeImage/' + ns + 'URL'))
    itemresult.imageurl = itemresult.medium_image_url
    itemresult.isbn = root.findtext('.//' + ns + 'ItemAttributes/' + ns + 'ISBN')
    if itemresult.isbn != None:
        itemresult.isbn = itemresult.isbn.strip()
    return itemresult

def item_lookup(title, author=''):
    itemresult = books_search(title, author)
    if itemresult == None:
        itemresult = blended_search(title, author)
    if itemresult == None:
        itemresult = books_search(title, None)
    if itemresult == None:
        itemresult = music_search(title, author)
    if itemresult == None:
        logging.error('item_lookup failed')
        itemresult = models.ItemResult()
        itemresult.source = 'amazon'
        itemresult.item_url = 'http://www.amazon.com/gp/search?keywords=' +  urllib.quote(title + ' ' + author)

    return itemresult



def main():	
    print itemurl('Love in the Ruins', 'Percy, Walker')


if __name__ == '__main__':
    main()
