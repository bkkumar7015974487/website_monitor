import os
import glob
import sys
from email.mime.text import MIMEText
import smtplib

from path import Path
from flask import url_for

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
        else:
            raise ValueError("website_name or website_slug needed")

        self.cfg = helper.get_cfg_urls()[self.name]
        self.url = self.cfg['url']
        self.css_selector = self.cfg['css_selector']
        self.files_dir = os.path.join(conf.DATA_DIR, self.slug)

        self.check_files = []
        if os.path.isdir(self.files_dir):
            with Path(self.files_dir):
                # check files
                files = glob.glob(f"*{conf.CHECK_FILE_ENDING}")
                for _file in files:
                    # collect diff files
                    diff_file = None
                    timestamp = _file.rstrip(conf.CHECK_FILE_ENDING)
                    diff_files = glob.glob(f"*{timestamp}*{conf.DIFF_FILE_ENDING}")
                    if len(diff_files) > 1:
                        helper.e(f"More than one diff files ({diff_files}) found for check_file ({_file})")
                    elif len(diff_files) == 1:
                        # create CheckFile
                        diff_file = diff_files[0]
                    self.check_files.append(CheckFile(self, _file, diff_file))

    def add_check_file(self, check_file_name):
        check_file = CheckFile(self, check_file_name)
        self.check_files.append(check_file)
        return check_file

    @property
    def last_change(self):
        for check_file in self.check_files:
            if check_file.has_diff_file:
                return check_file.diff_file.creation_date


    @property
    def diff_files_count(self):
        return sum([el.has_diff_file for el in self.check_files])

    def notify(self, html="n/t", debug=False):
        """Send Mail using smpts"""
        msg = MIMEText(html, 'html')
        msg['Subject'] = f"Change detected {self.name}"
        s = smtplib.SMTP_SSL(os.environ['MAIL_SMTP_SSL_HOST'])
        if debug:
            s.set_debuglevel(1)
        s.login(os.environ['MAIL_SMTP_USERNAME'], os.environ['MAIL_SMTP_PASSWORD'])
        s.sendmail('website_monitor@herokuapp.com','jan.hofmayer@mailbox.org', msg.as_string())
        s.quit()

    def get_threshold(self, tag, typee):
        try:
            return self.cfg['threshold'][tag][typee]
        except KeyError:
            return 0

    @staticmethod
    def all():
        websites = []
        for url_name in helper.get_cfg_urls():
            websites.append(Website(website_name=url_name))
        return websites


class File():
    def __init__(self, website, file_name):
        self.website = website
        self.file_name = file_name
        self.file_ending = None

    @property
    def file_path(self):
        return os.path.join(self.website.files_dir, self.file_name)

    @property
    def creation_date(self):
        timestamp = self.file_name.rstrip(self.file_ending)
        return helper.timestamp_to_human(timestamp)


class CheckFile(File):

    def __init__(self, website, file_name, diff_file=None):
        super().__init__(website, file_name)
        self.diff_file = DiffFile(website, diff_file) if diff_file else None
        self.file_ending = conf.CHECK_FILE_ENDING

    @property
    def has_diff_file(self):
        return self.diff_file != None

    def add_diff_file(self, diff_file_name):
        diff_file = DiffFile(self.website, diff_file_name)
        self.diff_file = diff_file
        return diff_file


class DiffFile(File):

    def __init__(self, website, file_name):
        super().__init__(website, file_name)
        self.file_ending = conf.DIFF_FILE_ENDING

    @property
    def url(self):
        return f"http://{helper.get_hostname()}/url/{self.website.slug}>/diff/{self.file_name}"

    @property
    def href(self):
        return f"<a href={self.url}>Open Diff</a>"
