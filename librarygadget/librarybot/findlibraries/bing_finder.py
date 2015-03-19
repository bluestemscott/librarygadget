import sys
import urllib
import json
import requests


class BingApiResult():
    def __init__(self, json_result):
        self.response = json.loads(json_result)['SearchResponse']['Web']
        self.total = self.response['Total']

    def find_libraries(self):
        libraries = []
        return self.response['Results']

    def eof(self):
        try:
            self.find_libraries()
            return False
        except KeyError as e:
            return True


        
def bing_search(search_terms, base_url, offset):
    base_url = base_url + "&Query=" + urllib.quote_plus(search_terms)
    url = base_url + "&Web.Count=50&Web.Offset=" + str(offset)
    print str(offset) + " " + url
    r = requests.get(url)
    search_result = BingApiResult(r.content)
    if search_result.eof():
        print "EOF"
        return []
    libraries = search_result.find_libraries()
    print 'Total results ' + str(search_result.total)
    print 'Current results ' + str(len(libraries))
    return libraries


def main():
    # for example, to search Bing for Horizon libraries: "inanchor:ipac20 account"
    search_terms = "inanchor:ipac20 -site:si.edu"
    if len(sys.argv) > 1:
        search_terms = sys.argv[1]
    base_url = "http://api.bing.net/json.aspx?AppId=91650C54158D791BE8B89E229B2190C53C83ABE8&Sources=Web&Version=2.0&Market=en-us&Adult=Moderate&Web.Options=DisableQueryAlterations"

    offset = 0
    libraries = []
    new_libraries = bing_search(search_terms, base_url, offset)
    while len(new_libraries) != 0:
        libraries.extend(new_libraries)
        offset += len(new_libraries)
        new_libraries = bing_search(search_terms, base_url, offset)

    for library in libraries:
        print library['Title'] + ',' + library['Url']

if __name__ == '__main__':
    main()