import os
import glob
import sys
import time
import requests

from path import Path
from bs4 import BeautifulSoup
from lxml.html.diff import htmldiff

import helper
import conf

class Website():
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
                _check_files = glob.glob(f"*{conf.CHECK_FILE_ENDING}")
                for check_file in _check_files:
                    # collect diff files
                    diff_file = None
                    timestamp = check_file.rstrip(conf.CHECK_FILE_ENDING)
                    diff_files = glob.glob(f"*{timestamp}*{conf.DIFF_FILE_ENDING}")
                    if len(diff_files) > 1:
                        helper.e(f"More than one diff files ({diff_files}) found for check_file ({check_file})")
                    elif len(diff_files) == 1:
                        diff_file = diff_files[0]
                    # create CheckFile
                    self.check_files.append(CheckFile(self, check_file, diff_file))

        self.clean_up()

    @property
    def last_change(self):
        for check_file in self.check_files:
            if check_file.has_diff_file:
                return check_file.diff_file.timestamp_human

    @property
    def diff_files(self):
        return list(filter(None.__ne__, [el.diff_file for el in self.check_files]))

    @property
    def diff_files_count(self):
        return len(self.diff_files)

    def clean_up(self):
        # remove every check_file which not has a diff_file depending on conf.MAX_CHECK_FILES
        if len(self.check_files) > conf.MAX_CHECK_FILES:
            idx = conf.MAX_CHECK_FILES - 1 # because we count from the back
            for check_file in self.check_files[:-idx]:
                if not check_file.has_diff_file:
                    os.remove(check_file.path)

        # remove diff file
        if len(self.diff_files) > conf.MAX_DIFF_FILES:
            idx = conf.MAX_DIFF_FILES - 1
            for diff_file in self.diff_files:
                os.remove(diff_file.path)
                # we do not delete orphaned check_files here, this will happen in the next clean_up run

    def add_check_file(self, check_file):
        if isinstance(check_file, CheckFile):
            self.check_files.append(check_file)
        else:
            raise ValueError('Must be of type CheckFile')

    def get_threshold(self, tag, typee):
        try:
            return self.cfg['threshold'][tag][typee]
        except KeyError:
            return 0

    def get_css_selector_soup(self):
        r = requests.get(self.url)
        soup = helper.get_soup(r.text)
        if self.css_selector:
            conts = soup.select(self.css_selector)
            html = " ".join([str(el) for el in conts])
            return html

    def get_diff(self):
        """Get diff between the latest to website.check_files"""
        hashes = []
        for _check_file in [ self.check_files[-2], self.check_files[-1] ]:
            soup = _check_file.soup

            if self.css_selector:
                cont = soup.select(self.css_selector)
                if len(cont) > 1:
                    sys.exit('!! selector not unique')
                if not cont:
                    sys.exit(f"!! selector '{self.css_selector}' no results")
                cont = cont[0]
            else:
                cont = soup.html()

            hashes.append(str(cont))

        diff = htmldiff(hashes[0], hashes[1])
        return BeautifulSoup(diff, 'lxml'), diff

    @staticmethod
    def all():
        websites = []
        for url_name in helper.get_cfg_urls():
            websites.append(Website(website_name=url_name))
        return websites


class File():
    def __init__(self, website, file_name=None):
        """If file_name is given, load"""
        self.website = website
        self.path = os.path.join(conf.DATA_DIR, website.slug, file_name) if file_name else None

        # abstract attribute
        self.ending = None

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def url(self):
        return f"http://{helper.get_hostname()}/url/{self.website.slug}/diff/{self.name}"

    @property
    def soup(self):
        html = open(self.path, encoding="utf-8")
        return helper.get_soup(html)

    @property
    def timestamp(self):
        return self.name.rstrip(self.ending)

    @property
    def timestamp_human(self):
        return helper.timestamp_to_human(self.timestamp)

    def create(self, content, timestamp=None):
        """Create new"""
        if not self.ending:
            raise ValueError("file_ending is None")
        if self.path:
            raise ValueError("path alread set")

        timestamp = timestamp if timestamp else time.time()
        os.makedirs(self.website.files_dir, exist_ok=True)
        self.path = os.path.join(self.website.files_dir, f"{timestamp}{self.ending}")
        with open(self.path, 'w', encoding="utf-8") as f:
            f.write(content)

        helper.p(f"Successfully written {self.path}")
        return self


class CheckFile(File):
    def __init__(self, website, check_file=None, diff_file=None):
        super().__init__(website, check_file)
        self.diff_file = DiffFile(website, diff_file) if diff_file else None
        self.ending = conf.CHECK_FILE_ENDING

    @property
    def has_diff_file(self):
        return self.diff_file != None

    def add_diff_file(self, diff_file):
        if isinstance(diff_file, DiffFile):
            self.diff_file = diff_file
        else:
            raise ValueError("diff_file must of be of type DiffFile")

    def create_diff_file(self, content):
        diff_file = DiffFile(self.website).create(content, self.timestamp)
        self.add_diff_file(diff_file)
        return diff_file


class DiffFile(File):
    def __init__(self, website, diff_file=None):
        super().__init__(website, diff_file)
        self.ending = conf.DIFF_FILE_ENDING

    @property
    def href(self):
        return f"<a href={self.url}>Open Diff</a>"

    def notify(self):
        html_content=f"<a href={self.url}>diff</a> for <a href={self.website.url}>{self.website.name}</a>"
        helper.sendmail(f"Change detected {self.name}", html_content)
        helper.push_bullet(f"Change detected", self.website.url)
        helper.push_bullet(f"Diff file", self.url)
