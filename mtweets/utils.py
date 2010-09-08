"""mtweets - Easy Twitter utilities in Python

mtweets is an up-to-date library for Python that wraps the Twitter API.
Other Python Twitter libraries seem to have fallen a bit behind, and
Twitter's API has evolved a bit. Here's hoping this helps.
"""

import functools
import urllib2

from urllib2 import HTTPError

try:
    import simplejson
except ImportError:
    raise Exception("mtweets requires the simplejson library (or Python 2.6) to work. http://www.undefined.org/python/")

try:
    from oauth import OAuthClient
    from oauth import OAuthError
    from oauth import OAuthConsumer
    from oauth import OAuthRequest
    from oauth import OAuthSignatureMethod_HMAC_SHA1
except ImportError:
    raise Exception("mtweets requires the oauth clien library to work. http://github.com/carlitux/Python-OAuth-Client")


############################################################################
## Base code
############################################################################

class TwitterClient(OAuthClient):
    
    def __init__(self, oauth_params, user_agent=None, desktop=False,
                 force_login=False, proxy=None, version=1):
        """
        Instantiates an instance of mtweets. Takes optional parameters for
        authentication and such (see below).

        Parameters:
            oauth_params - key, secret tokens for OAuth
            
            desktop - define if the API will be used for desktop apps or web apps.
            
            force_login -  Optional. Forces the user to enter their credentials
                           to ensure the correct users account is authorized.
                           
            user_agent - User agent header.
            
            proxy - An object detailing information, in case proxy 
                    user/authentication is required. Object passed should 
                    be something like...

            proxyobj = { 
                "username": "fjnfsjdnfjd",
                "password": "fjnfjsjdfnjd",
                "host": "http://fjanfjasnfjjfnajsdfasd.com", 
                "port": 87 
            } 

        version (number) - Twitter supports a "versioned" API as of 
                           Oct. 16th, 2009 - this defaults to 1, but can be 
                           overridden on a class and function-based basis.

        ** Note: versioning is not currently used by search.twitter functions; 
           when Twitter moves their junk, it'll be supported.
        """
        # setting super class variables
        OAuthClient.__init__(self, OAuthConsumer(*oauth_params), None)
        
        # setting the the needed urls
        self._url_request       = "https://api.twitter.com/oauth/request_token"
        self._url_access        = "https://api.twitter.com/oauth/access_token"
        self._url_autorize      = "https://api.twitter.com/oauth/authorize"
        self._url_authenticate  = "https://api.twitter.com/oauth/authenticate"
        
        self._signature_method = OAuthSignatureMethod_HMAC_SHA1()
        
        # subclass variables
        self.apiVersion = version
        self.proxy = proxy
        self.user_agent = user_agent
        self.desktop = desktop
        self.force_login = force_login
        
        if self.proxy is not None:
            self.proxyobj = urllib2.ProxyHandler({'http': 'http://%s:%s@%s:%d'%(self.proxy["username"], self.proxy["password"], self.proxy["host"], self.proxy["port"])})
            self.opener = urllib2.build_opener(self.proxyobj)
        else:
            self.opener = urllib2.build_opener()
            
        if self.user_agent is not None:
            self.opener.addheaders = [('User-agent', self.user_agent)]
        
    ############################################################################
    ## Super class implementation
    ############################################################################

    def _get_signature_method(self):
        return self._signature_method    

    def _get_request_request(self):
        """Return an OauthRequest instance to request the token"""
        return OAuthRequest.from_consumer_and_token(self.consumer, callback=None,
                                                    http_url=self._url_request)
    
    def _get_access_request(self):
        """Return an OauthRequest instance to authorize"""
        return OAuthRequest.from_consumer_and_token(self.consumer, 
                                                    token=self.token,
                                                    verifier=self.token.verifier,
                                                    http_url=self._url_access)
    
    def _get_authorize_request(self):
        params = {}
        if self.desktop:
            url = self._url_autorize
            params['oauth_callback'] = 'oob'
        else:
            url = self._url_authenticate
        if self.force_login:
                params['force_login'] = 'true'
        return OAuthRequest.from_consumer_and_token(self.consumer, 
                                                    token=self.token, 
                                                    http_url=url, 
                                                    parameters=params)
    
    def _get_resource_request(self, url, parameters, http_method='GET'):
        return OAuthRequest.from_consumer_and_token(self.consumer,
                                                    http_url=url,
                                                    token=self.token,
                                                    parameters=parameters,
                                                    http_method=http_method)

############################################################################
## Exceptions
############################################################################

class RequestError(Exception):
    def __init__(self, msg, error_code='0'):
        self.msg = msg
        self.error_code = error_code
        
    def __str__(self):
        return "Error code: %s -> %s"%(self.error_code, self.msg)

class AuthError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return str(self.msg)

############################################################################
## Decorators
############################################################################

def authentication_required(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.is_authorized():
            try:
                return simplejson.load(func(self, *args, **kwargs))
            except HTTPError, e:
                raise RequestError("%s(): %s"%(func.__name__, e.msg), e.code)
        else:
            raise AuthError("%s(): requires you to be authenticated"%(func.__name__))
    return wrapper

def simple_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:               
            return simplejson.load(func(self, *args, **kwargs))
        except HTTPError, e:
            raise RequestError("%s(): %s"%(func.__name__, e.msg), e.code)
    return wrapper