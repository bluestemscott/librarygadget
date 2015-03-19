from email.mime.text import MIMEText
from smtplib import SMTP
import logging
import time

def send_message(to, subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = 'Library Gadget <notifications@librarygadget.com>'
    msg['To'] = to
    send_email(msg)

def connect():
    server = SMTP('localhost')
    return server

def send_email(msg, server=None, disconnect=True):
    time.sleep(2) # so as to not exceed Amazon SES limits
    if server is None:
        server = connect()
    to_addrs = msg['To'].split(',')
    print msg.as_string()
    logging.info("about to send message")
    server.sendmail('notifications@librarygadget.com',to_addrs, msg.as_string())
    if disconnect:
        server.quit()
    logging.info("message sent")

def test(to, subject, body):
    print 'to: ' + to + ' subject: ' + subject + ' body: ' + body

message = \
"""%s has been added to the iGoogle library accounts gadget:  http://www.librarygadget.com.  Let me know if you have any trouble, and if you like it, spread the word!

-Scott
"""

def main():
    send_message("scollyp@gmail.com", 'Library gadget', message  % ("Test") )


if __name__ == '__main__':
    main()
