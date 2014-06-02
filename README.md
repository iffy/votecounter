# Vote Counter #

Here is a server that counts votes for a poll but that tries to prevent rampant
voting by machines.

## How to run it on Heroku ##

1. Clone this repo.

        git clone https://github.com/iffy/votecounter.git
        cd votecounter

2. Sign up for reCAPTCHA here: https://www.google.com/recaptcha/admin

3. Sign up for Heroku here: http://www.heroku.com.  It's free until you want it to not be free.

4. Read through these instructions *except step 4* to get set up: https://devcenter.heroku.com/articles/quickstart

5. Instead of step 4, create an app within this repo:

        heroku apps:create

6. Set your reCAPTCHA private key:

        heroku config:set CAPTCHA_PRIVATE_KEY="put yours here"

7. Choose the things people are allowed to vote on:

        heroku config:set VOTING_OPTIONS="round1-apple round1-banana round1-cow round1-dog"

8. Make a database

        heroku addons:add heroku-postgresql:dev

9. Add your SSH key:

        heroku keys:add

10. Run the app

        git push heroku master

11. See it:

        heroku apps:open
        # or if that fails
        heroku apps:info

12. Change other parameters to your liking (see `run.py` for a description)

        heroku config:set TOKENS_PER_IP=3 TOKEN_REFRESH_RATE=10 TOKEN_EXPIRATION=360


## The JavaScript ##

See `example.html` for an example of that JavaScript needed to interact with
the server.