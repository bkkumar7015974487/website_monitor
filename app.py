import os
import sys
from time import sleep
import threading
import requests
import logging

from flask import Flask, render_template, url_for, send_from_directory

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
        content=render_template('urls.html', websites=Website.all()))


@APP.route('/urls/start')
def urls_start():
    monitor.start()
    return render_template('index.html', content="monitor started")


@APP.route('/url/<website_slug>')
def url(website_slug):
    website = Website(website_slug=website_slug)
    return render_template(
        'index.html',
        content=render_template('url.html', website=website))


@APP.route('/url/<website_slug>/css_selector')
def url_css_selector(website_slug):
    website = Website(website_slug=website_slug)
    return website.get_css_selector_soup()


@APP.route('/url/<website_slug>/diff/<diff_name>')
def url_diff(website_slug, diff_name):
    return send_from_directory(os.path.join(conf.DATA_DIR, website_slug), diff_name)


@APP.route('/url/<website_slug>/checkfile/<checkfile_name>')
def url_checkfile(website_slug, checkfile_name):
    return send_from_directory(os.path.join(conf.DATA_DIR, website_slug), checkfile_name)


@APP.route('/ping')
def ping():
    return 'pong'


@APP.route('/sendmail')
def sendmail():
    helper.sendmail('test')
    return 'ok'


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
