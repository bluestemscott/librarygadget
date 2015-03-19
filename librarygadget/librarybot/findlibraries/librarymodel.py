from sys import argv
import re
import sqlite3
import requests
import BeautifulSoup
import worldcat


class Library():
    def __init__(self):
        self.name = ""
        self.home_url = ""
        self.home_html = ""
        self.catalog_url = ""
        self.opac = ""
        self.state = ""
        self.country = ""
        self.zip = ""
        self.worldcat_html = ""
        self.checked = False

    def ready_to_add(self):
        return self.is_opac_supported() and self.state is not None and self.state != ""

    def is_opac_supported(self):
        return self.opac in ('ipac',
                            'opac',
                            'webpacpro',
                            'polaris',
                            'koha')

    def sniff_ils(self):
        soup = BeautifulSoup.BeautifulSoup(self.home_html)
        link = soup.find('a', {'href':re.compile('/ipac20')})
        if link is not None:
            self.opac = 'ipac'
            self.catalog_url = link['href'].split('?')[0]
            self.catalog_url = self.catalog_url + "?menu=account"


        link = soup.find('a', {'href':re.compile('patroninfo')})
        if link is not None:
            self.opac = 'webpacpro'
            self.catalog_url = link['href']

        link = soup.find('a', {'href':re.compile('/cgisirsi')})
        if link is not None:
            self.opac = 'opac'
            self.catalog_url = link['href']

        link = soup.find('a', {'href':re.compile('polaris/logon.aspx')})
        if link is not None:
            self.opac = 'polaris'
            self.catalog_url = link['href']

        link = soup.find('a', {'href':re.compile('koha')})
        if link is not None:
            self.opac = 'koha'
            self.catalog_url = link['href']

        link = soup.find('a', {'href':re.compile('interpac.dll')})
        if link is not None:
            self.opac = 'interpac'
            self.catalog_url = link['href']

        link = soup.find('a', {'href':re.compile('Pwebrecon.cgi')})
        if link is not None:
            self.opac = 'pwebrecon'
            self.catalog_url = link['href']


def create_libraries_table():
    with sqlite3.connect('librarybot/findlibraries/libraries.db') as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE LIBRARIES
                       (NAME VARCHAR(150),
                       HOME_URL VARCHAR(150),
                       HOME_HTML TEXT,
                       CATALOG_URL VARCHAR(150),
                       OPAC VARCHAR(150),
                       CHECKED BOOLEAN)

        """)

def add_column():
    with sqlite3.connect('librarybot/findlibraries/libraries.db') as conn:
        c = conn.cursor()
        c.execute("""
            ALTER TABLE LIBRARIES
                ADD COLUMN
                ZIP VARCHAR(10)
        """)

class LibraryDao():
    def __init__(self, db='librarybot/findlibraries/libraries.db'):
        print db
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()

    def clear_all_opacs(self):
        self.cur.execute("""
            update libraries
            set catalog_url='', opac=''
        """
        )

    def insert_library(self, library):
        self.cur.execute("""
            insert into libraries
            values (?,?,?,?,?,?,?,?,?,?)""",
            (library.name,
             library.home_url,
             library.home_html,
             library.catalog_url,
             library.opac,
             library.checked,
            library.state,
            library.country,
            library.worldcat_html,
            library.zip,
            )
        )

    def map_from_row(self, row):
        library = Library()
        library.name = row[0]
        library.home_url = row[1]
        library.home_html = row[2]
        library.catalog_url = row[3]
        library.opac = row[4]
        library.checked = row[5]
        library.state = row[6]
        library.zip = row[7]
        library.country = row[8]
        library.worldcat_html = row[9]
        return library

    def retrieve_unchecked(self):
        self.cur.execute("select name, home_url, home_html, catalog_url, opac, checked, state, zip, country, worldcat_html from libraries where checked != 'True'")
        libraries = []
        for row in self.cur:
            libraries.append(self.map_from_row(row))
        return libraries

    def retrieve_all(self):
        self.cur.execute("""select name, home_url, home_html, catalog_url, opac, checked, state, zip, country, worldcat_html
                        from libraries
                        order by opac, name""")
        libraries = []
        for row in self.cur:
            libraries.append(self.map_from_row(row))
        return libraries

    def update_library(self, library):
        self.cur.execute("""
            update libraries
            set catalog_url=?, opac=?, checked=?, home_html=?, state=?, zip=?, country=?, worldcat_html=?
            where name=?""",
            (library.catalog_url,
            library.opac,
            library.checked,
            library.home_html,
            library.state,
            library.zip,
            library.country,
            library.worldcat_html,
            library.name)
        )



def find_opac_login_page(start_url):
    r = requests.get(start_url)
    library.home_html = r.content

def fix_opac_catalogs():
    libraryDao = LibraryDao()
    libraries = libraryDao.retrieve_all()
    libraries = [l for l in libraries if l.opac == 'opac']
    # this isn't a login page
    libraries = [l for l in libraries if l.catalog_url.find('/0/49')]
    for library in libraries:
        library.catalog_url = find_opac_login_page(library.catalog_url)
        libraryDao.update_library(library)


def resniff(libraryDao):
    libraryDao.clear_all_opacs()
    libraries = libraryDao.retrieve_all()
    for library in libraries:
        try:
            library.sniff_ils()
            print library.name + " - " + library.opac
            libraryDao.update_library(library)
        except Exception as e:
            print library.name + " - " + e.message
    libraryDao.conn.commit()


def update_worldcat_info(libraryDao):
    libraries = libraryDao.retrieve_all()
    libraries = [l for l in libraries if l.worldcat_html is None or len(l.worldcat_html)==0]
    for library in libraries[0:99]:
        worldcat_result = worldcat.library_search(library.name)
        print library.name + ' ' + str(worldcat_result)
        library.country = worldcat_result.country
        library.worldcat_html = worldcat_result.html
        library.state = worldcat_result.state_abbrev
        libraryDao.update_library(library)

    libraryDao.conn.commit()

def main():
    libraryDao = None
    if len(argv) > 1:
        libraryDao = LibraryDao(argv[1])
    else:
        libraryDao = LibraryDao()
    #resniff(libraryDao)
    #update_worldcat_info(libraryDao)
    libraries = libraryDao.retrieve_all()
    for library in libraries:
        if library.ready_to_add():
            print library.name + "," + library.catalog_url + "," + library.opac + ',' + library.state
            

if __name__ == '__main__':
    main()
  