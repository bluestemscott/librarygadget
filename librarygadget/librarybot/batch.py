# batch process
import time
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import traceback
import logging
import sys
import urllib

sys.path.insert(0, '/opt/librarygadget/venv/lib/python2.7/site-packages')

from django.db.models import Q
from librarybot.models import Patron
from librarybot.models import AccessLog
import librarybot.gmail

def get_patrons_to_run(today):
    patrons = Patron.objects.filter(user__userprofile__account_level='paid')
    patrons = patrons.filter(Q(batch_last_run__isnull=True) | Q(batch_last_run__lt=today))
    patrons = patrons.filter(inactive=False)
    return patrons

def pluralize(count, word):
    if count != 1:
        return word + 's'
    else:
        return word

def amazon_link(title, author):
    if author is None:
        author = ''
    return ''.join(["http://www.librarygadget.com/booklookup/amazon/redirect/?title=",
                                   urllib.quote_plus(title),
                                   "&author=",
                                   urllib.quote_plus(author)])

def find_overdue(items, today):
    return [item for item in items if item.dueDate<today]

def find_almost_due(items, today):
    almost_due_threshold = today + datetime.timedelta(days=2)
    almost_due_items = [item for item in items if (item.dueDate<=almost_due_threshold and item.dueDate>=today)]
    logging.info("finding almost due items: " + str(almost_due_items))
    return almost_due_items

def create_message(renewed, almost_due, overdue, today, to_addr):
    subject_parts = []
    plain_lines = []
    html_lines = []
    subject_parts.append('')

    if len(overdue) > 0:
        subject_parts.append('%i %s overdue' % (len(overdue), pluralize(len(overdue), 'item')))
        plain_lines.append('OVERDUE\n')
        html_lines.append('<b>Overdue</b><table cellspacing="0" cellpadding="6" border="0"><tr>')
        for item in overdue:
            days_late = today - item.dueDate
            plain_parts = (item.title, days_late.days, pluralize(days_late.days, 'day'), item.renewalError)
            plain_lines.append('"%s" -- %i %s overdue. %s\n\n' % plain_parts)
            html_parts = (amazon_link(item.title, item.author), item.title, days_late.days, pluralize(days_late.days, 'day'), item.renewalError)
            html_lines.append('<tr><td><a href="%s">%s</a></td><td>%i %s overdue</td><td>%s</td></tr>' % html_parts)
        plain_lines.append('\n')
        html_lines.append('</table><br/>')

    if len(almost_due) > 0:
        if len(subject_parts) > 1:
            subject_parts.append(', ')
        subject_parts.append('%i %s almost due' % (len(almost_due), pluralize(len(almost_due), 'item')))
        plain_lines.append('ALMOST DUE\n')
        html_lines.append('<b>Almost Due</b><table cellspacing="0" cellpadding="6" border="0"><tr>')
        for item in almost_due:
            days_due = item.dueDate - today
            plain_parts = (item.title, days_due.days, pluralize(days_due.days, 'day'), item.renewalError)
            plain_lines.append('"%s" -- %i %s to return. %s\n' % plain_parts)
            html_parts = (amazon_link(item.title, item.author), item.title, days_due.days, pluralize(days_due.days, 'day'), item.renewalError)
            html_lines.append('<tr><td><a href="%s">%s</a></td><td>%i %s to return</td><td>%s</td></tr>' % html_parts)
        plain_lines.append('\n')
        html_lines.append('</table><br/>')

    if len(renewed) > 0:
        if len(subject_parts) > 1:
            subject_parts.append(', ')
        subject_parts.append('%i %s auto-renewed' % (len(renewed), pluralize(len(renewed), 'item') ))
        plain_lines.append('AUTO-RENEWED\n')
        html_lines.append('<b>Auto Renewed</b><table cellspacing="0" cellpadding="6" border="0"><tr>')
        for item in renewed:
            new_date = item.dueDate.strftime("%m/%d")
            plain_parts = (item.title, new_date)
            plain_lines.append('"%s" -- new due date is %s\n' % plain_parts)
            html_parts = (amazon_link(item.title, item.author), item.title, new_date)
            html_lines.append('<tr><td><a href="%s">%s</a></td><td>New due date - %s</td></tr>' % html_parts)
        plain_lines.append('\n')
        html_lines.append('</table>')

    plain = ''.join(plain_lines)
    html = '\n'.join(html_lines)
    subject = ''.join(subject_parts)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'Library Gadget <notifications@librarygadget.com>'
    msg['To'] = to_addr

    part1 = MIMEText(plain, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    return msg


def process_patron(patron, today, smtp_server):
    items = patron.get_items_fresh()
    logging.info("Items length: " + str(len(items)))
    almost_due = find_almost_due(items, today)
    logging.info("Almost due: " + str(len(almost_due)))
    overdue = find_overdue(items, today)
    logging.info("Overdue: " + str(len(overdue)))
    if len(almost_due) == 0 and len(overdue) == 0:
        return

    #try to renew overdue and almost due items
    titles = [item.title for item in almost_due]
    titles.extend([item.title for item in overdue])
    renewal_result_items = patron.renew_items(patron.pin, patron.name, titles)
    not_renewed = [item for item in renewal_result_items if not item.renewed]
    renewed = [item for item in renewal_result_items if item.renewed]
    overdue = find_overdue(not_renewed, today)
    almost_due = find_almost_due(not_renewed, today)

    #notify patron
    msg = create_message(renewed, almost_due, overdue, today, patron.user.email)
    librarybot.gmail.send_email(msg, smtp_server, False)

    #record activity
    record_activity(patron, renewed, almost_due, overdue)



def run_batch():
    logging.info("Running librarybot batch")
    # even if this runs past midnight the batch_last_run date will be the same for all patrons
    today = datetime.date.today() 
    patrons = get_patrons_to_run(today)
    logging.info("Number of patrons to run: " + str(len(patrons)))
    smtp_server = librarybot.gmail.connect()
    for patron in patrons:
        try:
            logging.info("Patron: " + patron.patronid)
            process_patron(patron, today, smtp_server)
            patron.batch_last_run = today
            patron.save()
        except Exception as e:
            handle_exception(patron, e)
    smtp_server.quit()

def record_activity(patron, renewed, almost_due, overdue):
    access_log = AccessLog()
    access_log.patron = patron
    access_log.user = patron.user
    access_log.library = patron.library
    access_log.renewed_count = len(renewed)
    access_log.almost_due_count = len(almost_due)
    access_log.overdue_count = len(overdue)
    access_log.viewfunc = 'batch'
    access_log.save()

def handle_exception(patron, exception):
    if (str(exception).find('Library login failed') != -1):
      return
    logging.error(' '.join([patron.patronid, str(exception), traceback.format_exc().strip()[0:2999]]))
    # librarybot.gmail.send_message('scott@librarygadget.com,peterson.scott@principal.com', 'Batch failure', str(exception))
    access_log = AccessLog()
    access_log.patron = patron
    access_log.user = patron.user
    access_log.library = patron.library
    access_log.viewfunc = 'batch'
    access_log.error = str(exception)
    access_log.error_stacktrace = traceback.format_exc().strip()[0:2999]
    access_log.save()

if __name__ == '__main__':
    try:
        run_batch()
    except Exception as e:
        logging.error(''.join([str(e), traceback.format_exc().strip()[0:2999]]))
