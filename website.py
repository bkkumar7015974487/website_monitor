import os
import glob
import sys
from email.mime.text import MIMEText
import smtplib

from path import Path

import helper
import conf

class Website():
    """
    self.slug --> dir name
    """
    def __init__(self, website_name=None, website_slug=None):
        if website_name:
            self.name = website_name
            self.slug = helper.get_valid_filename(website_name)
        elif website_slug:
            for website_name in helper.get_cfg_urls():
                if helper.get_valid_filename(website_name) == website_slug:
                    self.name = website_name
                    break
            self.slug = website_slug

        self.cfg = helper.get_cfg_urls()[self.name]
        self.url = self.cfg['url']
        self.css_selector = self.cfg['css_selector']
        self.check_files_dir = os.path.join(conf.DATA_DIR, self.slug)

    @property
    def check_files(self):
        check_files = None
        with Path(self.check_files_dir):
            check_files = sorted(glob.glob(f"*{conf.CHECK_FILE_ENDING}"),)
        return check_files

    def find_diff_files(self, check_file=None):
        """find all diff files, optionally filtered for timestamp of given check_file"""
        diff_files = None
        with Path(self.check_files_dir):
            if check_file:
                timestamp = check_file.rstrip(conf.CHECK_FILE_ENDING)
                diff_files = glob.glob(f"*{timestamp}*{conf.DIFF_FILE_ENDING}")
                if len(diff_files) > 2:
                    helper.p(f"More than two diff_files found for given check_file={check_file}. This indicates a database inconsistecy.")
            else:
                diff_files = glob.glob(f"*{conf.DIFF_FILE_ENDING}")
        return diff_files

    @property
    def diff_files_count(self):
        return len(self.find_diff_files())

    def notify(self, text="n/t", debug=False):
        msg = MIMEText(text)
        msg['Subject'] = f"Change detected {self.name}"
        s = smtplib.SMTP_SSL(os.environ['MAIL_SMTP_SSL_HOST'])
        if debug:
            s.set_debuglevel(1)
        s.login(os.environ['MAIL_SMTP_USERNAME'], os.environ['MAIL_SMTP_PASSWORD'])
        s.sendmail('website_monitor@herokuapp.com','jan.hofmayer@mailbox.org', msg.as_string())
        s.quit()

