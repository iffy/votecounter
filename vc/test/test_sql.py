from twisted.trial.unittest import TestCase, SkipTest
from twisted.internet import reactor, defer
import os


from vc.error import NotAnOption
from vc.sql import SQLVoteStore


from sqlalchemy import create_engine
from alchimia import TWISTED_STRATEGY



def testEngine():
    url = os.environ.get('DATABASE_URL', None)
    if url is None:
        raise SkipTest('You must set DATABASE_URL in order to test')
    engine = create_engine(url, reactor=reactor, strategy=TWISTED_STRATEGY)
    return engine



class SQLVoteStoreTest(TestCase):


    @defer.inlineCallbacks
    def getStore(self, *args, **kwargs):
        engine = testEngine()
        store = SQLVoteStore(engine, *args, **kwargs)
        yield store.upgradeSchema()
        defer.returnValue(store)


    @defer.inlineCallbacks
    def test_vote(self):
        """
        You can vote for an option.
        """
        store = yield self.getStore(options=['foo'])
        yield store.vote('foo', '1.2.3.4')


    @defer.inlineCallbacks
    def test_vote_options(self):
        """
        You can only vote for whitelisted options.
        """
        store = yield self.getStore(options=['foo'])
        yield self.assertFailure(store.vote('bar', '1.2.3.4'), NotAnOption)


    @defer.inlineCallbacks
    def test_getResults(self):
        """
        You can get the current results.
        """
        store = yield self.getStore(options=['foo', 'bar', 'baz'])
        yield store.vote('foo', '1.2.3.4')
        yield store.vote('foo', '1.2.3.4')
        yield store.vote('bar', '1.2.3.4')
        results = yield store.getResults()
        self.assertEqual(results['foo'], 2)
        self.assertEqual(results['bar'], 1)
        self.assertEqual(results['baz'], 0)

