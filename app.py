from flask import Flask, render_template, url_for, render_template_string
from sparkpost import SparkPost
import os
import sys
from time import sleep
from concurrent.futures import ThreadPoolExecutor

import helper
import conf
import monitor

APP = Flask(__name__)

# per http://octomaton.blogspot.com/2014/07/hello-world-on-heroku-with-python.html

@APP.route('/')
def source():
    urls_data = []
    for url_name, url_config in helper.get_config_urls().items():
        urls_data.append({
            'url': url_config['url'],
            'name': url_name,
            'dir_name': helper.get_valid_filename(url_name)
        })
    return render_template(
        'index.html',
        content=render_template('urls.html', urls_data=urls_data)
        )

@APP.route('/url/<dir_name>')
def url(dir_name):
    check_files = []
    for check_file in helper.get_check_files(dir_name):
        diff_file = helper.find_diff_file(dir_name, check_file)
        if diff_file:
            diff_file = f'<a href={url_for("url_diff", dir_name=dir_name, diff_name=diff_file)}>Diff</a>'

        check_files.append({
            'name': check_file,
            'date': helper.check_file_to_date_human(check_file),
            'diff_file': diff_file
        })
    return render_template(
        'index.html',
        content=render_template('url.html', header=dir_name, check_files=check_files)
        )

@APP.route('/url/<dir_name>/diff/<diff_name>')
def url_diff(dir_name, diff_name):
    with open(os.path.join(conf.DATA_DIR, dir_name, diff_name)) as f:
        content = f.readlines()
    return render_template(
        'index.html',
        content=content[0]
    )

@APP.route('/send')
def send():
    sparky = SparkPost() # uses environment variable
    from_email = 'test@' + os.environ.get('SPARKPOST_SANDBOX_DOMAIN') # 'test@sparkpostbox.com'

    response = sparky.transmission.send(
        use_sandbox=True,
        recipients=['endymonium@gmail.com'],
        html='<html><body><p>Testing SparkPost - the world\'s most awesomest email service!</p></body></html>',
        from_email=from_email,
        subject='Oh hey!'
    )
    helper.p(response)
    return 'sent'

#
# Long Running Background Task
#
# EXECUTOR = ThreadPoolExecutor(2)

# def monitor_scheduler():
#     while True:
#         helper.p('ping')
#         monitor.start_async(helper.get_config_urls())
#         sleep(60)

def ping():
    while True:
        helper.p('ping')
        monitor.start_async(helper.get_config_urls())
        sleep(25)

import threading
if __name__ == "__main__":
    #EXECUTOR.submit(monitor_scheduler)
    thread = threading.Thread(
        target=ping
    )
    thread.start()
    # APP.run(threaded=True)
    APP.run(host='0.0.0.0')
