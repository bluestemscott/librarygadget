import urlparse

from librarybot.models import Library

def other_names(current_libraries, name, catalog_url):
    import_netloc = urlparse.urlparse(catalog_url).netloc
    return [l for l in current_libraries if l.name != name and urlparse.urlparse(l.catalogurl).netloc == import_netloc]

def in_current_list(current_libraries, name, catalog_url):
    catalog_netlocs = [urlparse.urlparse(l.catalogurl).netloc for l in current_libraries]
    names = [l.name for l in current_libraries]
    import_netloc = urlparse.urlparse(catalog_url).netloc
    return import_netloc in catalog_netlocs or name in names


def add(name, catalog_url, opac, state):
    library = Library()
    library.name = name.decode('utf-8')
    library.catalogurl = catalog_url.decode('utf-8')
    library.librarysystem = opac.decode('utf-8')
    library.active = True
    library.state = state
    library.pin_required = True
    library.renew_supported_code = True
    library.save()


def parse_line(line):
    line_split = line.split(',')
    lib = {}
    lib['name'] = line_split[0]
    lib['catalog_url'] = line_split[1]
    lib['opac'] = line_split[2]
    lib['state'] = line_split[3]
    return lib

def main(file='C:/hg/bluestem/librarygadget/librarybot/findlibraries/elf_libraries.txt'):
    current_libraries = Library.objects.all()
    with open(file) as f:
        lines = f.readlines()

        print('** New libraries')
        for line in lines:
            lib = parse_line(line)
            if not in_current_list(current_libraries, lib['name'], lib['catalog_url']):
                add(lib['name'], lib['catalog_url'], lib['opac'], lib['state'])
                print lib['name'] + " - " + lib['catalog_url'] + " - " + lib['opac'] + " - " + lib['state']

"""
        print('')
        print('** Libraries under other names')
        for line in lines:
            lib = parse_line(line)
            other_libs = other_names(current_libraries, lib['name'], lib['catalog_url'])
            for library in other_libs:
                print(lib['name'] + ' already there as ' + library.name)
"""

if __name__ == '__main__':
    main(argv[1])
