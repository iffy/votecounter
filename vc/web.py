from twisted.internet import defer
import treq
from klein import Klein

from functools import wraps

import json


def getIP(request):
    ip = request.getHeader('x-forwarded-for')
    if ip is None:
        ip = request.getClientIP()
    return ip


def jsonHandler(func):
    @wraps(func)
    @defer.inlineCallbacks
    def deco(instance, request, *args, **kwargs):
        callback_fn = request.args.get('callback', [None])[0]
        request.setHeader('Content-Type', 'application/json')
        try:
            result = yield func(instance, request, *args, **kwargs)
        except Exception as e:
            # XXX since jquery is awesome and doesn't handle error codes
            #request.setResponseCode(400)
            result = {'error': str(e)}
        result = json.dumps(result)
        if callback_fn:
            result = '%s(%s)' % (callback_fn, result)
        defer.returnValue(result)
    return deco


class VoteCounter(object):

    app = Klein()


    def __init__(self, vote_store, token_dispenser, captcha_verifier):
        self.vote_store = vote_store
        self.token_dispenser = token_dispenser
        self.captcha_verifier = captcha_verifier


    @app.route('/results')
    @jsonHandler
    @defer.inlineCallbacks
    def results(self, request):        
        results = yield self.vote_store.getResults()
        defer.returnValue(results)


    @app.route('/token', methods=['GET'])
    @jsonHandler
    @defer.inlineCallbacks
    def token(self, request):
        ip = getIP(request)
        captcha_challenge = request.args.get('recaptcha_challenge_field', [None])[0]
        captcha_response = request.args.get('recaptcha_response_field', [None])[0]
        token = None
        if captcha_challenge and captcha_response:
            yield self.captcha_verifier.assertVerified(
                ip, captcha_challenge, captcha_response)
            token = yield self.token_dispenser.getToken(ip, check_available=False)
        else:
            token = yield self.token_dispenser.getToken(ip)
        defer.returnValue({
            'token': token,
        })


    @app.route('/vote')
    @jsonHandler
    @defer.inlineCallbacks
    def vote(self, request):
        option = request.args.get('option', [None])[0]
        token = request.args.get('token', [None])[0]
        ip = getIP(request)
        if not token:
            raise Exception('You must provide a token')
        yield self.token_dispenser.useToken(token)
        yield self.vote_store.vote(option, ip)
        defer.returnValue({})



class RecaptchaVerifier(object):


    def __init__(self, private_key):
        self.private_key = private_key


    def assertVerified(self, ip, challenge, response):
        params = {
            'privatekey': self.private_key,
            'remoteip': ip,
            'challenge': challenge,
            'response': response,
        }
        response = yield treq.post('http://www.google.com/recaptcha/api/verify',
                params)
        content = yield treq.content(response)
        if not content.startswith('true\n'):
            raise Exception('Captcha failed')

