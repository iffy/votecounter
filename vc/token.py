
import uuid
from twisted.internet import defer, reactor


class Error(Exception): pass
class InvalidToken(Error): pass
class NoTokensLeft(Error): pass


NOTHING = object()


class MemoryStore(object):
    """
    I am an asynchronous, in-memory key-value store.
    """


    def __init__(self, clock=None):
        self._data = {}
        self.clock = clock

    
    def setValue(self, key, value):
        self._data[key] = value
        return defer.succeed(None)


    def getValue(self, key, default=NOTHING):
        if key in self._data:
            return defer.succeed(self._data[key])
        else:
            if default is NOTHING:
                return defer.fail(KeyError(key))
            else:
                return defer.succeed(default)


    def rmValue(self, key):
        del self._data[key]
        return defer.succeed(None)


    def exists(self, key):
        return defer.succeed(key in self._data)


    def increment(self, key, amount):
        """
        Increment a value by a certain amount.
        """
        if key not in self._data:
            self._data[key] = 0
        self._data[key] += amount
        return defer.succeed(self._data[key])


    def _maybeRemove(self, key):
        self._data.pop(key, None)


    def expire(self, key, seconds):
        """
        Set a key to expire in C{seconds} seconds.
        """
        self.clock.callLater(seconds, self._maybeRemove, key)



class TimedTokenDispenser(object):
    

    def __init__(self, available=3, refresh=60, use_limit=1, expiration=120,
            store=None, clock=reactor):
        """
        @param available: Number of tokens available per key.
        @param refresh: Seconds after which a token becomes available
            again for a particular key.
        @param use_limit: Number of times a token can be used.
        @param expiration: Seconds after which a token can't be used.
        """
        self.available = available
        self.refresh = refresh
        self.use_limit = use_limit
        self.expiration = expiration
        self.store = store
        self.clock = clock


    @defer.inlineCallbacks
    def getToken(self, key, check_available=True):
        """
        @param key: Some identifying key, like an IP address.
        @param check_available: If C{False} then return a token whether there
            is one available or not.
        """
        if check_available:
            key_key = 'K:' + key
            exists = yield self.store.exists(key_key)
            # XXX this exposes a race condition because some other process might
            # cause it to exist between this line and the next yield.
            if not exists:
                yield self.store.setValue(key_key, 3)
            tokens_left = yield self.store.increment(key_key, -1)
            if tokens_left <= 0:
                # XXX another race condition between the above yield and this
                yield self.store.increment(key_key, 1)
                raise NoTokensLeft('No tokens left')
            self.clock.callLater(self.refresh, self.store.increment, key_key, 1)

        # make a new token
        token = str(uuid.uuid4())
        token_key = 'TK:' + token
        yield self.store.increment(token_key, self.use_limit)
        yield self.store.expire(token_key, self.expiration)
        defer.returnValue(token)


    @defer.inlineCallbacks
    def useToken(self, token):
        token_key = 'TK:' + token
        uses_left = yield self.store.increment(token_key, -1)
        if uses_left <= 0:
            yield self.store.rmValue(token_key)
        if uses_left < 0:
            raise InvalidToken('Token already used')

