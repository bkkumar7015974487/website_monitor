# Website Monitor (work in progress)

When I'm big, I will be a deployable website monitor using the Heroku free tier.

Design goals:

* As simple as possible: no external database or scheduler
* Online but no running costs

## Set up

### Deploy to Heroku

1. Get a Heroku Account and add a credit card so that you get 1000h dyno hours for free
2. Install Heroku Toolbelt and `cd website_monitor`
3. Create a Heroku instance `heroku create` and note down the app name
4. Add dyno-metadata from Heroku Labs: `heroku labs:enable runtime-dyno-metadata -a <app name>`. This provides the `HEROKU_APP_NAME` environment variable, which we need for a pinger to prevent the app from idling.
5. Push to Heroku: `git push heroku master`

### to deploy or develop locally

1. Install the Python dependencies: `pip install -r requirements.txt`
2. Put some Heroku variables into a local .env file: `python fill_env.py`

Now you got multiple options:

* Just start the webserver: `python app.py`
* Start Heroku: `heroku local web -f Procfile`

## Configuration

```
MAIL_RECIPIENTS=<email1>,<email1>
MAIL_FROM=<email>
MAIL_SMTP_USERNAME=<usr>
MAIL_SMTP_PASSWORD=<pwd>
MAIL_SMTP_SSL_HOST=<host>:<port, usually 465>
```
