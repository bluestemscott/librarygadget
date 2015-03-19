import logging
import locale
import django
import os

from settings import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'librarygadget',
		'USER': 'root',
		'PASSWORD': '',
		'HOST': '127.0.0.1',
		'PORT': ''
	}
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        }
}

ROOT_URLCONF = 'urls'

logging.basicConfig(
    level = logging.INFO, # logging.WARNING,
    format = '%(asctime)s %(levelname)s %(message)s',
    filename = os.path.join(SITE_ROOT, '/var/log/librarygadget/trace.log'),
    filemode = 'ab+',
)


