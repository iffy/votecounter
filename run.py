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

    engine = create_engine(url, reactor=reactor, strategy=TWISTED_STRATEGY)
    store = SQLVoteStore(engine, ['foo', 'bar', 'baz'])
    yield store.upgradeSchema()

    captcha_verifier = RecaptchaVerifier(captcha_private)

    dispenser = TimedTokenDispenser(
        available=4,
        refresh=60,
        use_limit=4,
        expiration=240,
        store=MemoryStore(reactor),
    )
    app = VoteCounter(store, dispenser, captcha_verifier)
    site = Site(app.app.resource())
    reactor.listenTCP(9003, site)
    yield defer.Deferred()


task.react(start)