import os
import glob
from urllib.parse import urlparse
import datetime
import re
import sys
import smtplib
from email.mime.text import MIMEText

import yaml
from path import Path

import conf
from website import Website
from sparkpost import SparkPost

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
WEBSITES_YAML = 'websites.yaml'

def get_poller_interval():
    return int(os.getenv('POLLER_INTERVAL', 60))

def get_cfg():
    with open(f"{BASE_PATH}/{WEBSITES_YAML}", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg

def get_cfg_urls():
    return get_cfg()['urls']

# def p(*args):
#   print(args[0] % (len(args) > 1 and args[1:] or []))
#   sys.stdout.flush()
def p(arg):
  print(arg)
  sys.stdout.flush()


def check_file_to_date_human(check_file):
    """convert the filename, which is a timestamp, into a human date"""
    timestamp = check_file.rstrip(conf.CHECK_FILE_ENDING)
    return datetime.datetime.fromtimestamp(float(timestamp)).strftime('%d-%m-%Y %H:%M:%S')

def find_diff_file(dir_name, check_file):
    timestamp = check_file.rstrip(conf.CHECK_FILE_ENDING)
    check_files_dir = os.path.join(conf.DATA_DIR, dir_name)
    diff_files = None
    with Path(check_files_dir):
        print(f"*{timestamp}*{conf.DIFF_FILE_ENDING}")
        diff_files = glob.glob(f"*{timestamp}*{conf.DIFF_FILE_ENDING}")
    if diff_files:
        return diff_files[0]

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

def get_all_websites():
    websites = []
    for url_name in get_cfg_urls():
        websites.append(Website(website_name=url_name))
    return websites

def send_mail(subject, text='n/t', debug=False):
    msg = MIMEText(text)
    msg['Subject'] = subject
    s = smtplib.SMTP_SSL(os.environ['MAIL_SMTP_SSL_HOST'])
    if debug:
        s.set_debuglevel(1)
    s.login(os.environ['MAIL_SMTP_USERNAME'], os.environ['MAIL_SMTP_PASSWORD'])
    s.sendmail('website_monitor@herokuapp.com','jan.hofmayer@mailbox.org', msg.as_string())
    s.quit()
