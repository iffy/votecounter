# Vote Counter #

Here is a server that counts votes for a poll but that tries to prevent rampant
voting by machines.

## How to run it on Heroku ##

1. Clone this repo.

2. Sign up for reCAPTCHA here: https://www.google.com/recaptcha/admin

3. Sign up at http://www.heroku.com.  It's free until you want it to not be free.

4. Read through these instructions *except step 4* to get set up: https://devcenter.heroku.com/articles/quickstart

5. Instead of step 4, create an app within this repo:

    heroku apps:create

6. Set your reCAPTCHA private key:

    heroku config:set CAPTCHA_PRIVATE_KEY="put yours here"

7. Make a database

    heroku addons:add heroku-postgresql:dev

8. Run the app

    git push heroku master
