import sys
import urllib
import json
import requests
import BeautifulSoup

states = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AS': 'American Samoa',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'GU': 'Guam',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MP': 'Northern Mariana Islands',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NA': 'National',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'PR': 'Puerto Rico',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VI': 'Virgin Islands',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming',
    'AB': 'Alberta',
    'BC': 'British Columbia',
    'MB': 'Manitoba',
    'NB': 'New Brunswick',
    'NL': 'Newfoundland and Labrador',
    'NT': 'Northwest Territories',
    'NS': 'Nova Scotia',
    'NU': 'Nunavut',
    'ON': 'Ontario',
    'PE': 'Prince Edward Island',
    'QC': 'Quebec',
    'SK': 'Saskatchewan',
    'YT': 'Yukon Territory'
}


states_by_name = dict((v,k) for k, v in states.iteritems())

class WorldcatResult():
    def __init__(self, library_name, html):
        self.city = u''
        self.state = u''
        self.state_abbrev = u''
        self.zip = u''
        self.name = library_name
        self.country = u''
        self.html = html
        self.soup = BeautifulSoup.BeautifulSoup(html)
        self.parse()

    def parse(self):
        library_tr = self.soup.find('tr', {'id': self.name})
        if library_tr is None:
            #print 'library not found'
            return
        address = library_tr.find('p', {'class':'lib-search-address'})
        lines = address.findAll(text=True)
        #print lines
        #[u'\n             1000 Grand Avenue&nbsp;\n                 ', u'DES MOINES, Iowa&nbsp;50309', u'United States', u'(515) 283-4152']
        city_state_index = 0
        for x in range(0, len(lines)-1):
            if len(lines[x].split(',')) > 1:
                city_state_index = x
                break
        if city_state_index == 0:
            print address.prettify()
            print lines
            return

        self.country = lines[city_state_index+1]
        parts = lines[city_state_index].split(',')
        self.city = parts[0]
        if self.country in (u'United States', u'Canada'):
            self.state = parts[1].split('&')[0].strip()
            self.state_abbrev = states_by_name[self.state]
            self.zip = lines[city_state_index].split(';')[1]

    def __str__(self):
        return ''.join([' state=', self.state, ',', self.state_abbrev,
                        ' zip=',  self.zip,
                        ' city=', self.city,
                        ' country=', self.country])



        
def library_search(library_name):
    url = "http://www.worldcat.org/wcpa/servlet/org.oclc.lac.ui.ajax.ServiceServlet?serviceCommand=librarySearch&start=1&count=none&libType=none&dofavlib=false&sort=none&search="
    url +=  urllib.quote_plus(library_name)
    #print url
    r = requests.get(url)
    worldcat_result = WorldcatResult(library_name, r.content)
    return worldcat_result



def main():
    #library_search('Des Moines Public Library')
    f = open('worldcat_result.htm')
    worldcat_result = WorldcatResult('Des Moines Public Library', f.read())
    print worldcat_result

if __name__ == '__main__':
    main()