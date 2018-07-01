import os
import sys
from time import sleep
import threading
import requests
import logging

from flask import Flask, render_template, url_for, render_template_string

import helper
import conf
import monitor
from website import Website

"""Loosly based on http://octomaton.blogspot.com/2014/07/hello-world-on-heroku-with-python.html"""

APP = Flask(__name__)

# enable Heroku logging by directing log messages to stdout
# https://gist.github.com/seanbehan/547f5fc599bde304c89694a98c102bab
if helper.in_heroku():
    APP.logger.addHandler(logging.StreamHandler(sys.stdout)) # pylint: disable=E1101
    APP.logger.setLevel(logging.ERROR) # pylint: disable=E1101


@APP.route('/')
def source():
    return render_template(
        'index.html',
        content=render_template('urls.html', websites=helper.get_all_websites())
        )


@APP.route('/urls/start')
def urls_start():
    monitor.start()
    return render_template(
        'index.html',
        content="monitor started"
        )


@APP.route('/url/<website_slug>')
def url(website_slug):
    check_files = []
    helper.p('ping')
    website = Website(website_slug=website_slug)
    helper.p(website.name)
    for check_file in website.check_files:
        diff_files = ''
        for diff_file in website.find_diff_files(check_file):
            diff_files += f'<a href={url_for("url_diff", website_slug=website_slug, diff_name=diff_file)}>Diff</a>'

        check_files.append({
            'name': check_file,
            'date': helper.check_file_to_date_human(check_file),
            'diff_files': diff_files
        })
    return render_template(
        'index.html',
        content=render_template('url.html', header=website.name, check_files=check_files)
        )


@APP.route('/url/<website_slug>/diff/<diff_name>')
def url_diff(website_slug, diff_name):
    with open(os.path.join(conf.DATA_DIR, website_slug, diff_name)) as f:
        content = f.readlines()
    return render_template(
        'index.html',
        content=content[0]
    )


@APP.route('/ping')
def ping():
    return 'pong'


def poller():
    """Poor mans scheduler, runs continously in the background and triggers our monitoring jobs"""
    while True:
        monitor.start()

        # we ping ourselves to prevent the dyno from idling
        # this only works when the dyno-metadata plugin was added to the app
        if 'HEROKU_APP_NAME' in os.environ:
            requests.get(f"http://{os.environ['HEROKU_APP_NAME']}.herokuapp.com/ping")

        helper.p(f"Run finished, next in {helper.get_poller_interval()}s")
        sleep(helper.get_poller_interval())

if __name__ == "__main__":
    if helper.in_heroku():
        # start scheduler / poller
        thread = threading.Thread(target=poller)
        thread.start()
        APP.run(host='0.0.0.0', port=os.environ['PORT'])
    else:
        os.environ["FLASK_ENV"] = "development"
        APP.run()
