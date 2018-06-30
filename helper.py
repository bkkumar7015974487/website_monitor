import os
import glob
from urllib.parse import urlparse
import datetime
import re
import sys

import yaml
from path import Path

import conf

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
WEBSITES_YAML = 'websites.yaml'

#
# yaml
#
def get_css_selector(url_name):
    cfg = _get_yaml()
    urls = []
    for url_name in [ el for el in cfg['urls'] ]:
        urls.append(cfg['urls'][url_name]['css_selector'])
    return urls

def _get_yaml():
    with open(f"{BASE_PATH}/{WEBSITES_YAML}", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg

#
# debug print & verbosity
#
def p(*args):
  print(args[0] % (len(args) > 1 and args[1:] or []))
  sys.stdout.flush()


#
# urls
#
def get_check_files(url_dir):
    check_files = None
    check_files_dir = os.path.join(conf.DATA_DIR, url_dir)
    with Path(check_files_dir):
        check_files = sorted(glob.glob(f"*{conf.CHECK_FILE_ENDING}"),)
    return check_files

def get_config_urls():
    cfg = _get_yaml()
    return cfg['urls']

#
# check files
#
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

#
# Various
#
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