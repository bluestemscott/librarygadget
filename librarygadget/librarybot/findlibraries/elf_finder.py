import requests
import BeautifulSoup
import librarymodel


def store_elf_libraries(libraryDao):
    with open('libraryelf_libraries.htm') as f:
        html = f.read()
        soup = BeautifulSoup.BeautifulSoup(html)
        links = soup.findAll('a', {'title':'Go to library'})
        for link in links:
            library = librarymodel.Library()
            library.name = link.text
            library.home_url = link['href']
            libraryDao.insert_library(library)


def initial_load():
    libraryDao = librarymodel.LibraryDao()
    store_elf_libraries(libraryDao)
    libraries = libraryDao.retrieve_unchecked()
    for library in libraries:
        try:
            r = requests.get(library.home_url)
            library.home_html = r.content
            libraryDao.update_library(library)
        except Exception as e:
            print e


def main():
    #initial_load()
    pass

if __name__ == '__main__':
    main()
  