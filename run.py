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

    engine = create_engine(url, reactor=reactor, strategy=TWISTED_STRATEGY)
    store = SQLVoteStore(engine, options)
    yield store.upgradeSchema()

    captcha_verifier = RecaptchaVerifier(captcha_private)

    dispenser = TimedTokenDispenser(
        available=4,
        refresh=60,
        # Set this to the total number of votes that can be cast.
        use_limit=4,
        expiration=240,
        store=MemoryStore(reactor),
    )
    app = VoteCounter(store, dispenser, captcha_verifier, 'example.html')
    site = Site(app.app.resource())
    reactor.listenTCP(port, site)
    yield defer.Deferred()


task.react(start)