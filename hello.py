from flask import Flask
from sparkpost import SparkPost
import os

APP = Flask(__name__)

# per http://octomaton.blogspot.com/2014/07/hello-world-on-heroku-with-python.html

@APP.route('/')
def source():
    html = 'Hello World!'
    return html

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

    return response
