# Website Monitor (work in progress)

When I'm big, I will be a deployable website monitor using the Heroku free tier.

Design goals:

* As simple as possible: no external database or scheduler
* Online but no running costs

## Set up

### Deploy to Heroku

1. Get a Heroku Account
2. Install Heroku Toolbelt and `cd website_monitor`
3. Create a Heroku instance `heroku create` and note down the url
4. Add [Sparkline](https://elements.heroku.com/addons/sparkpost) (for sending E-Mails): `heroku addons:create sparkpost`
5. Push to Heroku: `git push heroku master`

### to deploy or develop locally

1. Install the Python dependencies: `pip install -r requirements.txt`
2. Put some Heroku variables into a local .env file: `python fill_env.py`

Now you got multiple options:

* Just start the webserver: `python app.py`
* Start Heroku: `heroku local web -f Procfile`

## Configuration
