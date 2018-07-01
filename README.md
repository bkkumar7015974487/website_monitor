# Website Monitor (alpha)

When I'm big, I will be a deployable website monitor using the Heroku free tier.

Design goals:

* As simple as possible: no external database or scheduler
* Online but no running costs

## Quickstart

### 1. Preparation

1. Get a Heroku Account and add a credit card so that you get 1000h dyno hours for free. No worries, it will not be charged.
2. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) and `cd website_monitor`
3. Create a Heroku instance `heroku create`, note down the app name
4. Add dyno-metadata from Heroku Labs: `heroku labs:enable runtime-dyno-metadata -a <app name>`. This provides the `HEROKU_APP_NAME` environment variable, which we need to prevent the app from idling.

### 2. Configuration

#### .env file

Create a `.env` file in the project root and add the following variables:

```bash
MAIL_RECIPIENTS=<email1>,<email1>,etc
MAIL_FROM=<email>
MAIL_SMTP_USERNAME=<usr>
MAIL_SMTP_PASSWORD=<pwd>
MAIL_SMTP_SSL_HOST=<host>:<port, usually 465>
```

After you are done, these env vars must be mirrored into Heroku. You can do that manually using the Heroku dashboard or use `python env_to_heroku.py`.

#### The websites

Add some websites to `websites.yaml`.

### 3. Deploy

`git push heroku master`

## How to deploy or develop locally

1. Install the Python dependencies: `pip install -r requirements.txt`

Now you got multiple options:

* Just start the webserver: `python app.py`
* Start Heroku: `heroku local web -f Procfile`