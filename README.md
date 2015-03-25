# Library Gadget

This is a tool I wrote a long time ago to learn Python. I used it privately for a while and then eventually hosted it at www.librarygadget.com. In 2013 I stopped maintaining it and in 2014 I shut down the site.

Library Gadget's killer feature is auto-renewal of library books. It lets users provide their library account usernames and passwords. It then runs a daily batch job to log into their accounts, check for any nearly due items, and automatically renew them if possible. If it can't renew them, it sends the user an email.

The library account scrapers supported hundreds of libraries at one time. They may or may not still work.

Library Gadget is a Django app, with all the core code in librarygadget/librarybot. This has model classes that let people sign up, pay, and view their library accounts. It also has a model that tracks items checked out for each library patron, and a batch script (batch.py) that checks every patron's account and tries to auto-renew. Finally, the library scapers are in librarygadget/librarybot: horizon.py, koha.py, opac.py, sirsidynix.py, and webpacpro.py.

