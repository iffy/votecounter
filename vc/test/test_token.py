from twisted.trial.unittest import TestCase
from twisted.internet import task, defer


from vc.token import TimedTokenDispenser, MemoryStore, InvalidToken
from vc.token import NoTokensLeft



class MemoryStoreTest(TestCase):


    @defer.inlineCallbacks
    def test_basic(self):
        store = MemoryStore()
        yield store.setValue('foo', 5)
        value = yield store.getValue('foo')
        self.assertEqual(value, 5)


    def test_KeyError(self):
        store = MemoryStore()
        self.assertFailure(store.getValue('foo'), KeyError)


    @defer.inlineCallbacks
    def test_rmValue(self):
        store = MemoryStore()
        yield store.setValue('foo', 5)
        yield store.rmValue('foo')
        yield self.assertFailure(store.getValue('foo'), KeyError)


    @defer.inlineCallbacks
    def test_getValue_default(self):
        store = MemoryStore()
        result = yield store.getValue('foo', 'default')
        self.assertEqual(result, 'default')


    @defer.inlineCallbacks
    def test_increment(self):
        """
        You can increment an integer value.
        """
        store = MemoryStore()
        result = yield store.increment('foo', 1)
        self.assertEqual(result, 1)
        result = yield store.increment('foo', 1)
        self.assertEqual(result, 2)
        result = yield store.increment('foo', -10)
        self.assertEqual(result, -8)


    @defer.inlineCallbacks
    def test_expire(self):
        """
        You can cause keys to expire.
        """
        clock = task.Clock()
        store = MemoryStore(clock=clock)
        yield store.setValue('foo', 'bar')
        yield store.expire('foo', 50)
        clock.advance(49)
        result = yield store.getValue('foo')
        self.assertEqual(result, 'bar')
        clock.advance(1)
        yield self.assertFailure(store.getValue('foo'), KeyError)


    @defer.inlineCallbacks
    def test_exists(self):
        """
        You can ask if a key exists.
        """
        store = MemoryStore()
        exists = yield store.exists('foo')
        self.assertEqual(exists, False)
        yield store.setValue('foo', 'bar')
        exists = yield store.exists('foo')
        self.assertEqual(exists, True)



class TimedTokenDispenserTest(TestCase):


    @defer.inlineCallbacks
    def test_getToken_unique(self):
        """
        You can get tokens from the dispenser which are unique.
        """
        d = TimedTokenDispenser(store=MemoryStore(task.Clock()),
            clock=task.Clock())
        t1 = yield d.getToken('foo')
        t2 = yield d.getToken('foo')
        self.assertNotEqual(t1, t2)


    @defer.inlineCallbacks
    def test_useToken(self):
        """
        You can use tokens.
        """
        d = TimedTokenDispenser(store=MemoryStore(task.Clock()),
            clock=task.Clock())
        t1 = yield d.getToken('foo')
        yield d.useToken(t1)


    @defer.inlineCallbacks
    def test_useToken_uses(self):
        """
        Tokens may only be used a certain number of times.
        """
        d = TimedTokenDispenser(use_limit=3, store=MemoryStore(task.Clock()),
            clock=task.Clock())
        token = yield d.getToken('foo')
        yield d.useToken(token)
        yield d.useToken(token)
        yield d.useToken(token)
        yield self.assertFailure(d.useToken(token), InvalidToken)


    @defer.inlineCallbacks
    def test_tokenExpires(self):
        """
        Tokens expire after a certain amount of time.
        """
        clock = task.Clock()
        d = TimedTokenDispenser(expiration=50, store=MemoryStore(clock),
            clock=clock)
        token = yield d.getToken('foo')
        clock.advance(50)
        yield self.assertFailure(d.useToken(token), InvalidToken)


    @defer.inlineCallbacks
    def test_getToken_limitByKey(self):
        """
        Tokens are limited in number according to the key.
        """
        clock = task.Clock()
        d = TimedTokenDispenser(available=2, store=MemoryStore(clock),
            clock=clock)
        yield d.getToken('foo')
        yield d.getToken('foo')
        yield self.assertFailure(d.getToken('foo'), NoTokensLeft)
        yield d.getToken('bar')


    @defer.inlineCallbacks
    def test_getToken_replenish(self):
        """
        Tokens are replenished over time.
        """
        clock = task.Clock()
        d = TimedTokenDispenser(available=2, refresh=10,
            store=MemoryStore(clock),
            clock=clock)
        yield d.getToken('foo')
        clock.advance(5)
        yield d.getToken('foo')
        yield self.assertFailure(d.getToken('foo'), NoTokensLeft)
        clock.advance(5)
        yield d.getToken('foo')
        yield self.assertFailure(d.getToken('foo'), NoTokensLeft)
        clock.advance(5)
        yield d.getToken('foo')


    @defer.inlineCallbacks
    def test_getToken_bypass(self):
        """
        You can bypass the getToken available amount.
        """
        clock = task.Clock()
        d = TimedTokenDispenser(available=2, refresh=10,
            store=MemoryStore(clock),
            clock=clock)
        yield d.getToken('foo')
        clock.advance(5)
        yield d.getToken('foo')
        yield self.assertFailure(d.getToken('foo'), NoTokensLeft)
        yield d.getToken('foo', check_available=False)



