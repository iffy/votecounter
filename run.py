from twisted.internet import task, defer
from twisted.python import log
from twisted.web.server import Site

import os
import sys

from alchimia import TWISTED_STRATEGY
from sqlalchemy import create_engine

from vc.sql import SQLVoteStore
from vc.token import TimedTokenDispenser, MemoryStore
from vc.web import VoteCounter, RecaptchaVerifier


@defer.inlineCallbacks
def start(reactor):
    log.startLogging(sys.stdout)
    url = os.environ.get('DATABASE_URL', None)
    if url is None:
        raise Exception('You must set DATABASE_URL')

    captcha_private = os.environ.get('CAPTCHA_PRIVATE_KEY', None)
    if captcha_private is None:
        raise Exception("You must provide a CAPTCHA_PRIVATE_KEY")

    options = os.environ.get('VOTING_OPTIONS', '').split()
    if not options:
        raise Exception("You must provide a space-separated list of VOTING_OPTIONS")

    port = int(os.environ.get('PORT', 9003))

    # Number of tokens per IP.  In other words, you can have this many people
    # vote from the same IP for ever TOKEN_REFRESH_RATE seconds.
    tokens_per_ip = int(os.environ.get('TOKENS_PER_IP', 4))

    # This is the number of seconds after which a token for a particular IP
    # can be used again.
    token_refresh_rate = int(os.environ.get('TOKEN_REFRESH_RATE', 60))

    # Number of votes that can be cast per voting token.
    use_limit = len(options) / 2

    # After a user gets a voting token, they have this many seconds to use it
    # before it won't work anymore.
    token_expiration = int(os.environ.get('TOKEN_EXPIRATION', 240))

    engine = create_engine(url, reactor=reactor, strategy=TWISTED_STRATEGY)
    store = SQLVoteStore(engine, options)
    yield store.upgradeSchema()

    captcha_verifier = RecaptchaVerifier(captcha_private)

    dispenser = TimedTokenDispenser(
        available=tokens_per_ip,
        refresh=token_refresh_rate,
        use_limit=use_limit,
        expiration=token_expiration,
        store=MemoryStore(reactor),
    )
    app = VoteCounter(store, dispenser, captcha_verifier, 'example.html')
    site = Site(app.app.resource())
    reactor.listenTCP(port, site)
    yield defer.Deferred()


task.react(start)