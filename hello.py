from flask import Flask

APP = Flask(__name__)

# per http://octomaton.blogspot.com/2014/07/hello-world-on-heroku-with-python.html

@APP.route('/')
def source():
    html = 'Hello World!'
    return html
