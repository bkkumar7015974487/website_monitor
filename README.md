# Website Monitor (alpha)

Website monitor using the Heroku free tier.

Design goals:

* As simple as possible
* Online but no running costs
* Configurable thresholds and selectors
* Different nofications, currently implemented are via E-mail and [Pushbullet](https://www.pushbullet.com)

## 1. Preparation

1. Get a Heroku Account and add a credit card so that you get 1000h dyno hours for free. No worries, it will not be charged.
2. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) and `cd website_monitor`
3. Create a Heroku instance `heroku create`, note down the app name
4. Add dyno-metadata from Heroku Labs: `heroku labs:enable runtime-dyno-metadata -a <app name>`. This provides the `HEROKU_APP_NAME` environment variable, which we need to prevent the app from idling.

## 2. Configuration

### `.env`

Create a `.env` file in the project root and add variables as needed


```bash
# how often the websites are checked, optional, default=300
POLLER_INTERVAL=300
```

After you are done, these env vars must be mirrored into Heroku. You can do that manually using the Heroku dashboard or use `python env_to_heroku.py`.

#### E-Mail Notifications

Put this into the `.env` file:

```bash
MAIL_ON=True
MAIL_RECIPIENTS=<email1>,<email1>,etc
MAIL_FROM=<email>
MAIL_SMTP_USERNAME=<usr>
MAIL_SMTP_PASSWORD=<pwd>
MAIL_SMTP_SSL_HOST=<host>:<port, usually 465>
```

#### Pushbullet Notifications

1. Create free account on [Pushbullet](https://www.pushbullet.com)
2. Edit the `.env` file:

```bash
PUSHBULLET_ON=True
PUSHBULLET_API_KEY=<generated access token>
```

### `websites.yaml`

Add some websites to `websites.yaml`. See file for example.

## 3. Deploy

`git push heroku master`

## How to deploy or develop locally

1. Install the Python dependencies: `pip install -r requirements.txt`

Now you got multiple options:

* Just start the webserver: `python app.py`
* Start Heroku: `heroku local web -f Procfile`