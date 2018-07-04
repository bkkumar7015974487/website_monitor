import os
import glob
from urllib.parse import urlparse
import datetime
import re
import sys
import time

import yaml
from path import Path
from email.mime.text import MIMEText
from email import utils
import smtplib

import conf

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
WEBSITES_YAML = 'websites.yaml'

def get_poller_interval():
    return int(os.getenv('POLLER_INTERVAL', 300))

def get_cfg():
    with open(f"{BASE_PATH}/{WEBSITES_YAML}", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg

def get_cfg_urls():
    return get_cfg()['urls']

def get_hostname():
    if in_heroku():
        return f"{os.environ['HEROKU_APP_NAME']}.herokuapp.com"
    else:
        return "localhost:5000"

# def p(*args):
#   print(args[0] % (len(args) > 1 and args[1:] or []))
#   sys.stdout.flush()
def p(arg):
  print(arg)
  sys.stdout.flush()

def e(arg):
  print(f"ERROR {arg}")
  sys.stdout.flush()


def timestamp_to_human(timestamp):
    return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%d-%m-%Y %H:%M:%S')

def get_valid_filename(s):
    """
    from https://github.com/django/django/blob/master/django/utils/text.py
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def in_heroku():
    """return true if running in Heroku"""
    # or 'PORT'
    return 'DYNO' in os.environ

def sendmail(subject, html_content='n/t', debug=False):
    """Send Mail using smpts"""
    # recipients_environ = os.environ['RECIPIENTS']
    recipients = os.environ['MAIL_RECIPIENTS'].split(',')

    msg = MIMEText(html_content, 'html')
    msg['Subject'] = subject
    msg['From'] = conf.APP_NAME
    msg['To'] = ", ".join(recipients)
    msg['Date'] = utils.formatdate(localtime=True)
    s = smtplib.SMTP_SSL(os.environ['MAIL_SMTP_SSL_HOST'])
    if debug:
        s.set_debuglevel(1)
    s.login(os.environ['MAIL_SMTP_USERNAME'], os.environ['MAIL_SMTP_PASSWORD'])
    s.sendmail('website_monitor@herokuapp.com', recipients, msg.as_string())
    s.quit()
    p(f"Send mail to {recipients} with subject={subject}")