#!/usr/bin/python

"""mtweets - Easy Twitter utilities in Python

mtweets is an up-to-date library for Python that wraps the Twitter API.
Other Python Twitter libraries seem to have fallen a bit behind, and
Twitter's API has evolved a bit. Here's hoping this helps.

Please review the online twitter docs for concepts used by twitter:

    http://developer.twitter.com/doc

like as Tweet entities, and how use each parameter
"""

import httplib, urllib, urllib2, mimetypes, mimetools

from urlparse import urlparse
from urllib2 import HTTPError

__author__ = "Luis C. Cruz <carlitos.kyo@gmail.com>"
__version__ = "0.1"

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

class RequestError(Exception):
    def __init__(self, msg, error_code='0'):
        self.msg = msg
        self.error_code = error_code
        
    def __str__(self):
        return "Error code: %s\n%s"%(self.error_code, self.msg)

class AuthError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)


class API(OAuthClient):
    """ This handle simple authentication flow.
    
    For desktop application should set the verifier field into the token 
    returned by fetch_for_authorize method before call fetch_access_token method.    
    
    >>> import mtweet
    
    Desktop applications:
    
    * request for access tokens datastore_object should be the instance that 
      manage user token set the right user token to avoid security problems.
    
    >>> api = mtweet.API((key, secret), 'my app', True)
    >>> api.oauth_datastore = datastore_object
    >>> url, token = api.fetch_for_authorize()
    >>> token.set_verifier(pin)
    >>> api.fetch_access_token(token)
    
    Web applications:
    
    * request for access tokens datastore_object should be the instance that 
      manage user token set the right user token to avoid security problems
    
    >>> api = mtweet.API((key, secret), 'my app')
    >>> api.oauth_datastore = datastore_object
    >>> url, token = api.fetch_for_authorize() # redirect url
    >>> api.fetch_access_token(token) # call in a url, restore the token and then fetch for access
    
    Fetch for resources
    
    >>> api = mtweet.API((key, secret), 'my app', True)
    >>> api.oauth_datastore = datastore_object
    >>> print api.verify_credentials()
    
    """
    
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
    ## some extra requests
    ############################################################################
    
    # URL Shortening function huzzah
    def shorten_url(self, url_to_shorten, shortener="http://is.gd/api.php",
                    query="longurl"):
        """shorten_url(url_to_shorten, shortener="http://is.gd/api.php", query="longurl")

        Shortens url specified by url_to_shorten.

        Parameters:
            url_to_shorten - URL to shorten.
            
            shortener - In case you want to use a url shortening service other
                        than is.gd.
        """
        try:
            template = "%s?%s"%(shortener, urllib.urlencode({query: self.unicode2utf8(url_to_shorten)}))
            return self.opener.open(template).read()
        except HTTPError, e:
            raise RequestError("shorten_url(): %s"%e.msg, e.code)
    
        
    def verify_credentials(self, version=None):
        """ verify_credentials(self, version=None):

        Verifies the authenticity of the passed in credentials. Used to be a 
        forced call, now made optional (no need to waste network resources)

        Parameters:
            None
        """
        version = version or self.apiVersion
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/account/verify_credentials.json" % version))
            except HTTPError, e:
                raise RequestError("verify_credentials(): %s"%e.msg, e.code)
        else:
            raise AuthError("verify_credentials() requires authorization.")

        
    ############################################################################
    ## Timeline methods
    ############################################################################
    
    def get_public_timeline(self, version=None, **kwargs):
        """get_public_timeline()

        Returns the 20 most recent statuses, including retweets if they exist,
        from non-protected users.
        
        The public timeline is cached for 60 seconds. Requesting more frequently
        than that will not return any more data, and will count against your 
        rate limit usage.

        Parameters:
            trim_user  -  When set to either true, t or 1, each tweet returned
                          in a timeline will include a user object including 
                          only the status authors numerical ID. Omit this 
                          parameter to receive the complete user object.
                          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node 
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            if len(kwargs) > 0:
                url = "http://api.twitter.com/%d/statuses/public_timeline.json?%s"%(version, urllib.urlencode(kwargs))
            else:
                url = "http://api.twitter.com/%d/statuses/public_timeline.json"%version                
            return simplejson.load(self.opener.open(url))
        except HTTPError, e:
            raise RequestError("get_public_timeline(): %s"%e.msg, e.code)
        
        
    def get_home_timeline(self, version=None, **kwargs):
        """get_home_timeline()

        Returns the 20 most recent statuses, including retweets if they exist,
        posted by the authenticating user and the user's they follow. This is
        the same timeline seen by a user when they login to twitter.com.

        Usage note: This method is identical to statuses/friends_timeline, 
        except that this method always includes retweets..
        This method is can only return up to 800 statuses, including retweets.

        Parameters:
            since_id - Returns results with an ID greater than (that is, 
                       more recent than) the specified ID. There are limits to
                       the number of Tweets which can be accessed through the 
                       API. If the limit of Tweets has occured since the 
                       since_id, the since_id will be forced to the oldest ID 
                       available.
                       
            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.
          
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 200.
          
            page - Specifies the page of results to retrieve.
            
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to 
                        receive the complete user object.
           include_entities - When set to either true, t or 1, each tweet will
                              include a node called "entities,". This node 
                              offers a variety of metadata about the tweet in a
                              discreet structure, including: user_mentions,
                              urls, and hashtags. While entities are opt-in on
                              timelines at present, they will be made a default
                              component of output in the future. See Tweet
                              Entities for more detail on entities.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/home_timeline.json"%version, kwargs))
            except HTTPError, e:
                raise RequestError("get_home_timeline(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_home_timeline() requires you to be authenticated.")
      
        
    def get_friends_timeline(self, version=None, **kwargs):
        """get_friends_timeline()

        Returns the 20 most recent statuses posted by the authenticating user
        and the user's they follow. This is the same timeline seen by a user
        when they login to twitter.com.
        
        This method is identical to statuses/home_timeline, except that this 
        method will only include retweets if the include_rts parameter is set.
        The RSS and Atom responses will always include retweets as statuses
        prefixed with RT.

        This method is can only return up to 800 statuses. If include_rts is set
        only 800 statuses, including retweets if they exist, can be returned.

        Parameters:
            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the 
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.
          
            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.
          
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 200.
                    
            page - Specifies the page of results to retrieve.
          
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to 
                        receive the complete user object.
                        
            include_rts - When set to either true, t or 1,the timeline will 
                          contain native retweets (if they exist) in addition to
                          the standard stream of tweets. The output format of
                          retweeted tweets is identical to the representation
                          you see in home_timeline. Note: If you're using the
                          trim_user parameter in conjunction with include_rts,
                          the retweets will still contain a full user object.
          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.is_authorized() is True:
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/friends_timeline.json"%version, kwargs))
            except HTTPError, e:
                raise RequestError("get_friends_timeline(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_friends_timeline() requires you to be authenticated.")
        
    
    def get_user_timeline(self, id=None, version=None, **kwargs): 
        """get_user_timeline(id=None)

        Returns the 20 most recent statuses posted by the authenticating user.
        It is also possible to request another user's timeline by using the
        screen_name or user_id parameter. The other users timeline will only be
        visible if they are not protected, or if the authenticating user's
        follow request was accepted by the protected user.

        The timeline returned is the equivalent of the one seen when you view a
        user's profile on twitter.com.

        This method is can only return up to 3200 statuses. If include_rts is
        set only 3200 statuses, including retweets if they exist, can be returned.

        This method will not include retweets in the XML and JSON responses 
        unless the include_rts parameter is set. The RSS and Atom responses will
        always include retweets as statuses prefixed with RT.


        Parameters:
            user_id - The ID of the user for whom to return results for.
                      Helpful for disambiguating when a valid user ID is also
                      a valid screen name.
                       
            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID.
                          
            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.
          
            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.
                     
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 200.
          
            page - Specifies the page of results to retrieve.
          
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.
          
            include_rts - When set to either true, t or 1,the timeline will
                          contain native retweets (if they exist) in addition to
                          the standard stream of tweets. The output format of
                          retweeted tweets is identical to the representation
                          you see in home_timeline. Note: If you're using the
                          trim_user parameter in conjunction with include_rts,
                          the retweets will still contain a full user object.
          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
            
        Parameters preferences: id, user_id, screen_name. If id is set then other parameters are ignored and so on.
        """
        version = version or self.apiVersion
        userTimelineURL = "http://api.twitter.com/%d/statuses/user_timeline.json"%version
        if id is not None:
            # clean not necesary parameters
            if 'user_id' in kwargs: del kwargs['user_id']
            if 'screen_name' in kwargs: del kwargs['screen_name']
            userTimelineURL = "http://api.twitter.com/%d/statuses/user_timeline/%s.json"%(version, id)
        elif 'user_id' in kwargs:
            # clean not necesary parameters
            if 'screen_name' in kwargs: del kwargs['screen_name']
        
        try:
            return simplejson.load(self.fetch_resource(userTimelineURL, kwargs))
        except HTTPError, e:
            raise RequestError("get_user_timeline(): %s"%e.msg, e.code)
        
    
    def get_mentions(self, version=None, **kwargs):
        """get_mentions()

        Returns the 20 most recent mentions (status containing @username) for
        the authenticating user.

        The timeline returned is the equivalent of the one seen when you view
        your mentions on twitter.com.

        This method is can only return up to 800 statuses. If include_rts is set
        only 800 statuses, including retweets if they exist, can be returned.

        This method will not include retweets in the XML and JSON responses
        unless the include_rts parameter is set. The RSS and Atom responses will
        always include retweets as statuses prefixed with RT.

        Parameters:
            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.
          
            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.
          
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 200.
          
            page - Specifies the page of results to retrieve.
          
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.
          
            include_rts - When set to either true, t or 1,the timeline will
                          contain native retweets (if they exist) in addition
                          to the standard stream of tweets. The output format
                          of retweeted tweets is identical to the representation
                          you see in home_timeline. Note: If you're using the
                          trim_user parameter in conjunction with include_rts,
                          the retweets will still contain a full user object.
          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in
                               on timelines at present, they will be made a
                               default component of output in the future. See
                               Tweet Entities for more detail on entities.

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/mentions.json"%version, kwargs))
            except HTTPError, e:
                raise RequestError("get_mentions(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_mentions() requires authorization.")
        
    
    def get_retweeted_of_me(self, version=None, **kwargs):
        """get_retweeted_of_me()

        Returns the 20 most recent tweets of the authenticated user that have
        been retweeted by others.

        Parameters:
            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.
          
            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.
          
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 100.
          
            page - Specifies the page of results to retrieve.
          
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.
          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
          
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.

        """
        version = version or self.apiVersion
        
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/retweets_of_me.json"%version, kwargs))
            except HTTPError, e:
                raise RequestError("get_retweeted_of_me(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_retweeted_of_me() requires authorization.")
        

    def get_retweeted_by_me(self, version=None, **kwargs):
        """get_retweeted_by_me()

        Returns the 20 most recent retweets posted by the authenticating user.

        Parameters:
            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.
          
            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.
          
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 100.
          
            page - Specifies the page of results to retrieve.
          
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.
                        
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
          
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.

        """
        version = version or self.apiVersion
        
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/retweeted_by_me.json"%version, kwargs))
            except HTTPError, e:
                raise RequestError("get_retweeted_by_me(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_retweeted_by_me() requires authorization.")
        

    def get_retweeted_to_me(self, version=None, **kwargs):
        """get_retweeted_to_me()

        Returns the 20 most recent retweets posted by users the authenticating
        user follow.

        Parameters:
            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.
          
            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.
          
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 100.
                    
            page - Specifies the page of results to retrieve.
          
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.
          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
          
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/retweeted_to_me.json"%version, kwargs))
            except HTTPError, e:
                raise RequestError("get_retweeted_to_me(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_retweeted_to_me() requires authorization.")
        
        
    ############################################################################
    ## Status methods
    ############################################################################
    
    def status_show(self, id, version=None, **kwargs):
        """status_show()

        Returns a single status, specified by the id parameter below. The 
        status's author will be returned inline.

        Parameters:
            id - The numerical ID of the desired status.
            
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to 
                        receive the complete user object.
                        
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        
        try:
            return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/show/%d.json"%(version, id), kwargs))
        except HTTPError, e:
            raise RequestError("status_show(): %s"%e.msg, e.code)
        
    
    def status_update(self, status, version=None, **kwargs):
        """status_update(status)

        Updates the authenticating user's status. A status update with text
        identical to the authenticating user's text identical to the
        authenticating user's current status will be ignored to prevent duplicates.


        Parameters:
            status - The text of your status update, up to 140 characters.
                     URL encode as necessary. 
                     
            in_reply_to_status_id - The ID of an existing status that the update
                                    is in reply to.
            lat - The latitude of the location this tweet refers to. This
                  parameter will be ignored unless it is inside the range
                  -90.0 to +90.0 (North is positive) inclusive. It will also be
                  ignored if there isn't a corresponding long parameter.
            
            long - The longitude of the location this tweet refers to. The valid
                   ranges for longitude is -180.0 to +180.0 (East is positive)
                   inclusive. This parameter will be ignored if outside that
                   range, if it is not a number, if geo_enabled is disabled,
                   or if there not a corresponding lat parameter.

            place_id - A place in the world. These IDs can be retrieved from
                       geo/reverse_geocode.

            display_coordinates - Whether or not to put a pin on the exact
                                  coordinates a tweet has been sent from.

            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.

            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['status'] = status
        
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/update.json"%version, kwargs, 'POST'))
            except HTTPError, e:
                raise RequestError("status_update(): %s"%e.msg, e.code)
        else:
            raise AuthError("status_update() requires authorization.")
        

    def status_destroy(self, id, version=None, **kwargs):
        """status_destroy(id)

        Destroys the status specified by the required ID parameter.
        Usage note: The authenticating user must be the author of the specified status.

        Parameters:
            id - The numerical ID of the desired status.
            
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.

            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/destroy/%s.json"%(version, id), kwargs, 'POST'))
            except HTTPError, e:
                raise RequestError("status_destroy(): %s"%e.msg, e.code)
        else:
            raise AuthError("status_destroy() requires authorization.")        
        
    
    def status_retweet(self, id, version=None, **kwargs):
        """status_retweet(id)

        Retweets a tweet. Returns the original tweet with retweet details embedded.
        
        Parameters:
            id - The numerical ID of the desired status. 
            
            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.
          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in
                               a discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
          
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/retweet/%s.json"%(version, id), kwargs, 'POST'))
            except HTTPError, e:
                raise RequestError("status_retweet(): %s"%e.msg, e.code)
        else:
            raise AuthError("status_retweet() requires authorization.")
        
    
    def get_retweets(self, id, version=None, **kwargs):
        """get_retweets(id):
    
        Returns up to 100 of the first retweets of a given tweet.

        Parameters:
            id - The numerical ID of the desired status. 
            
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 100.

            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.

            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/retweets/%s.json"%(version, id), kwargs))
            except HTTPError, e:
                raise RequestError("get_retweets(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_retweets() requires authorization.")

        
    def get_retweeted_by(self, id, version=None, **kwargs):
        """get_retweeted_by(id):
    
        Show user objects of up to 100 members who retweeted the status.

        Parameters:
            id - The numerical ID of the desired status. 
            
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 100.

            page - Specifies the page of results to retrieve.

            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.

            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/%s/retweeted_by.json"%(version, id), kwargs))
            except HTTPError, e:
                raise RequestError("get_retweeted_by(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_retweeted_by() requires authorization.")
    
    def get_retweeted_by_ids(self, id, version=None, **kwargs):
        """get_retweeted_by_ids(id):
    
        Show user ids of up to 100 users who retweeted the status.

        Parameters:
            id - The numerical ID of the desired status. 
            
            count - Specifies the number of records to retrieve. Must be less
                    than or equal to 100.

            page - Specifies the page of results to retrieve.

            trim_user - When set to either true, t or 1, each tweet returned in
                        a timeline will include a user object including only the
                        status authors numerical ID. Omit this parameter to
                        receive the complete user object.

            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.is_authorized():
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/%s/retweeted_by/ids.json"%(version, id), kwargs))
            except HTTPError, e:
                raise RequestError("get_retweeted_by_ids(): %s"%e.msg, e.code)
        else:
            raise AuthError("get_retweeted_by_ids() requires authorization.")
        
    
    ###########################################################################################################
    ## User methods
    ###########################################################################################################
        
    def user_show(self, user_id=None, screen_name=None, version=None, **kwargs):
        """user_show(user_id=None, screen_name=None)

        Returns extended information of a given user, specified by ID or screen
        name as per the required id parameter. The author's most recent status
        will be returned inline.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on 
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.

        Usage Notes:
        Requests for protected users without credentials from 
            1) the user requested or
            2) a user that is following the protected user will omit the nested status element.

        ...will result in only publicly available data being returned.
        """
        if user_id is None and screen_name is None:
            raise RequestError('user_show(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
                    
        try:
            return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/users/show.json"%(version), kwargs))
        except HTTPError, e:
            raise RequestError("user_show(): %s"%e.msg, e.code)
    
    
    def user_lookup(self, ids=None, screen_names=None, version=None, **kwargs):
        """user_lookup(ids=None, screen_names=None)
        
        Return up to 100 users worth of extended information, specified by
        either ID, screen name, or combination of the two. The author's most
        recent status (if the authenticating user has permission) will be
        returned inline.
        
        Parameters:
            user_id - A comma separated list of user IDs, up to 100 are allowed 
                      in a single request. Should be iterable object.

            screen_name - A comma separated list of screen names, up to 100 are
                          allowed in a single request. Should be iterable object.
            
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.

        Statuses for the users in question will be returned inline if they exist.
        Requires authentication!
        """
        version = version or self.apiVersion
        if self.is_authorized():
            if ids is not None:
                kwargs['user_id'] = ','.join(ids)
            if screen_names is not None:
                kwargs['screen_name'] = ','.join(screen_names)
            try:
                # do a POST request this beacuse the parameters can overflow the maximum GET length
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/users/lookup.json"%version, kwargs, 'POST'))
            except HTTPError, e:
                raise RequestError("user_lookup(): %s"%e.msg, e.code)
        else:
            raise AuthError("user_lookup() requires authorization.")
        
    def user_search(self, query, version=None, **kwargs):
        """user_search(query)
        
        Runs a search for users similar to Find People button on Twitter.com.
        The results returned by people search on Twitter.com are the same as
        those returned by this API request.

        Only the first 1000 matches are available.
        
        Parameters:
            query - The search query to run against people search. 

            per_page - The number of people to retrieve. Maxiumum of 20 allowed
                       per page.

            page - Specifies the page of results to retrieve.

            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
                    
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.is_authorized():
            kwargs['q'] = query
            try:
                return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/users/search.json"%version, kwargs))
            except HTTPError, e:
                raise RequestError("user_search(): %s"%e.msg, e.code)
        else:
            raise AuthError("user_search() requires authorization.")
        
    def user_suggestions(self, version=None):
        """user_suggestions()
        
        Access to Twitter's suggested user list. This returns the list of
        suggested user categories. The category can be used in the
        users/suggestions/category endpoint to get the users in that category.
        
        Parameters:
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/users/suggestions.json"%version))
        except HTTPError, e:
            raise RequestError("user_suggestions(): %s"%e.msg, e.code)
        
    def user_suggestions_slug(self, slug, version=None):
        """user_suggestions_slug(slug)
        
        Access the users in a given category of the Twitter suggested user list.
        It is recommended that end clients cache this data for no more than one
        hour.
        
        Parameters:
            slug - The short name of list or a category 
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/users/suggestions/%s.json"%(version, slug)))
        except HTTPError, e:
            raise RequestError("user_suggestions_slug(): %s"%e.msg, e.code)
        
    def user_profile_image(self, screen_name, version=None, **kwargs):
        """user_profile_image(screen_name)
        
        Access the profile image in various sizes for the user with the
        indicated screen_name. If no size is provided the normal image is
        returned. This resource does not return JSON or XML, but instead returns
        a 302 redirect to the actual image resource.
        
        This method should only be used by application developers to lookup or
        check the profile image URL for a user. This method must not be used as
        the image source URL presented to users of your application.

        Parameters:
            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID.
                          
            size - Specifies the size of image to fetch. Not specifying a size
                   will give the default, normal size of 48px by 48px. Valid
                   options include:

                       * bigger - 73px by 73px
                       * normal - 48px by 48px
                       * mini - 24px by 24px
                       
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/users/profile_image/%s.json"%(version, screen_name), kwargs))
        except HTTPError, e:
            raise RequestError("user_profile_image(): %s"%e.msg, e.code)
        
    def user_statuses_friends(self, version=None, **kwargs):
        """user_statuses_friends()
        
        Returns a user's friends, each with current status inline. They are
        ordered by the order in which the user followed them, most recently
        followed first, 100 at a time. (Please note that the result set isn't
        guaranteed to be 100 every time as suspended users will be filtered out.)

        Use the cursor option to access older friends.

        With no user specified, request defaults to the authenticated user's
        friends. It is also possible to request another user's friends list via
        the id, screen_name or user_id parameter.


        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID.

            cursor - Breaks the results into pages. This is recommended for
                     users who are following many users. Provide a value of
                     -1 to begin paging. Provide values as returned in the
                     response body's next_cursor and previous_cursor attributes
                     to page back and forth in the list.

            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities. 
                            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
                               
        Note.- unless requesting it from a protected user; if getting this
               data of a protected user, you must auth (and be allowed to see
               that user).
        """
        version = version or self.apiVersion
        try:
            return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/friends.json"%(version), kwargs))
        except HTTPError, e:
            raise RequestError("user_statuses_friends(): %s"%e.msg, e.code)
        
    
    def user_statuses_followers(self, version=None, **kwargs):
        """user_statuses_followers()
               
        Returns the authenticating user's followers, each with current status
        inline. They are ordered by the order in which they followed the user,
        100 at a time. (Please note that the result set isn't guaranteed to be
        100 every time as suspended users will be filtered out.)

        Use the cursor parameter to access earlier followers.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.
          
            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID.
          
            cursor - Breaks the results into pages. This is recommended for
                     users who are following many users. Provide a value of -1
                     to begin paging. Provide values as returned in the response
                     body's next_cursor and previous_cursor attributes to page
                     back and forth in the list.
          
            include_entities - When set to either true, t or 1, each tweet will
                               include a node called "entities,". This node
                               offers a variety of metadata about the tweet in a
                               discreet structure, including: user_mentions,
                               urls, and hashtags. While entities are opt-in on
                               timelines at present, they will be made a default
                               component of output in the future. See Tweet
                               Entities for more detail on entities.
                            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
                               
        Note.- unless requesting it from a protected user; if getting this
               data of a protected user, you must auth (and be allowed to see
               that user).
        """
        version = version or self.apiVersion
        try:
            return simplejson.load(self.fetch_resource("http://api.twitter.com/%d/statuses/followers.json"%(version), kwargs))
        except HTTPError, e:
            raise RequestError("user_statuses_followers(): %s"%e.msg, e.code)
        
    ###########################################################################################################
    ## List methods
    ###########################################################################################################
    
    ###########################################################################################################
    ## List members methods
    ###########################################################################################################
    
    ###########################################################################################################
    ## List subscribers methods
    ###########################################################################################################
    
    ###########################################################################################################
    ## Direct messages methods
    ###########################################################################################################
    
    ###########################################################################################################
    ## Friendship methods
    ###########################################################################################################
    
    ###########################################################################################################
    ## Social graph methods
    ###########################################################################################################

    def getRateLimitStatus(self, checkRequestingIP = True, version = None):
        """getRateLimitStatus()

        	Returns the remaining number of API requests available to the requesting user before the
        	API limit is reached for the current hour. Calls to rate_limit_status do not count against
        	the rate limit.  If authentication credentials are provided, the rate limit status for the
        	authenticating user is returned.  Otherwise, the rate limit status for the requesting
        	IP address is returned.

        	Params:
        		checkRequestIP - Boolean, defaults to True. Set to False to check against the currently requesting IP, instead of the account level.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion	
        try:
            if checkRequestingIP is True:
                return simplejson.load(urllib2.urlopen("http://api.twitter.com/%d/account/rate_limit_status.json" % version))
            else:
                if self.authenticated is True:
                    return simplejson.load(self.opener.open("http://api.twitter.com/%d/account/rate_limit_status.json" % version))
                else:
                    raise mtweetsError("You need to be authenticated to check a rate limit status on an account.")
        except HTTPError, e:
            raise mtweetsError("It seems that there's something wrong. Twitter gave you a %s error code; are you doing something you shouldn't be?" % `e.code`, e.code)
   

    def reportSpam(self, id = None, user_id = None, screen_name = None, version = None):
        """reportSpam(self, id), user_id, screen_name):

        	Report a user account to Twitter as a spam account. *One* of the following parameters is required, and
        	this requires that you be authenticated with a user account.

        	Parameters:
        		id - Optional. The ID or screen_name of the user you want to report as a spammer.
        		user_id - Optional.  The ID of the user you want to report as a spammer. Helpful for disambiguating when a valid user ID is also a valid screen name.
        		screen_name - Optional.  The ID or screen_name of the user you want to report as a spammer. Helpful for disambiguating when a valid screen name is also a user ID.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            # This entire block of code is stupid, but I'm far too tired to think through it at the moment. Refactor it if you care.
            if id is not None or user_id is not None or screen_name is not None:
                try:
                    apiExtension = ""
                    if id is not None:
                        apiExtension = "id=%s" % id
                    if user_id is not None:
                        apiExtension = "user_id=%s" % `user_id`
                    if screen_name is not None:
                        apiExtension = "screen_name=%s" % screen_name
                    return simplejson.load(self.opener.open("http://api.twitter.com/%d/report_spam.json" % version, apiExtension))
                except HTTPError, e:
                    raise mtweetsError("reportSpam() failed with a %s error code." % `e.code`, e.code)
            else:
                raise mtweetsError("reportSpam requires you to specify an id, user_id, or screen_name. Try again!")
        else:
            raise AuthError("reportSpam() requires you to be authenticated.")

    def searchUsers(self, q, per_page = 20, page = 1, version = None):
        """ searchUsers(q, per_page = None, page = None):

        	Query Twitter to find a set of users who match the criteria we have. (Note: This, oddly, requires authentication - go figure)

        	Parameters:
        		q (string) - Required. The query you wanna search against; self explanatory. ;)
        		per_page (number) - Optional, defaults to 20. Specify the number of users Twitter should return per page (no more than 20, just fyi)
        		page (number) - Optional, defaults to 1. The page of users you want to pull down.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/users/search.json?q=%s&per_page=%d&page=%d" % (version, q, per_page, page)))
            except HTTPError, e:
                raise mtweetsError("searchUsers() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("searchUsers(), oddly, requires you to be authenticated.")

    

    

    def getFriendsStatus(self, id = None, user_id = None, screen_name = None, page = None, cursor="-1", version = None):
        """getFriendsStatus(id = None, user_id = None, screen_name = None, page = None, cursor="-1")

        	Returns a user's friends, each with current status inline. They are ordered by the order in which they were added as friends, 100 at a time. 
        	(Please note that the result set isn't guaranteed to be 100 every time, as suspended users will be filtered out.) Use the page option to access 
        	older friends. With no user specified, the request defaults to the authenticated users friends. 

        	It's also possible to request another user's friends list via the id, screen_name or user_id parameter.

        	Note: The previously documented page-based pagination mechanism is still in production, but please migrate to cursor-based pagination for increase reliability and performance.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, or screen_name)
        		id - Optional. The ID or screen name of the user for whom to request a list of friends. 
        		user_id - Optional. Specfies the ID of the user for whom to return the list of friends. Helpful for disambiguating when a valid user ID is also a valid screen name.
        		screen_name - Optional. Specfies the screen name of the user for whom to return the list of friends. Helpful for disambiguating when a valid screen name is also a user ID.
        		page - (BEING DEPRECATED) Optional. Specifies the page of friends to receive.
        		cursor - Optional. Breaks the results into pages. A single page contains 100 users. This is recommended for users who are following many users. Provide a value of  -1 to begin paging. Provide values as returned to in the response body's next_cursor and previous_cursor attributes to page back and forth in the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = ""
            if id is not None:
                apiURL = "http://api.twitter.com/%d/statuses/friends/%s.json" % (version, id)
            if user_id is not None:
                apiURL = "http://api.twitter.com/%d/statuses/friends.json?user_id=%s" % (version, `user_id`)
            if screen_name is not None:
                apiURL = "http://api.twitter.com/%d/statuses/friends.json?screen_name=%s" % (version, screen_name)
            try:
                if page is not None:
                    return simplejson.load(self.opener.open(apiURL + "&page=%s" % `page`))
                else:
                    return simplejson.load(self.opener.open(apiURL + "&cursor=%s" % cursor))
            except HTTPError, e:
                raise mtweetsError("getFriendsStatus() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("getFriendsStatus() requires you to be authenticated.")

    def getFollowersStatus(self, id = None, user_id = None, screen_name = None, page = None, cursor = "-1", version = None):
        """getFollowersStatus(id = None, user_id = None, screen_name = None, page = None, cursor = "-1")

        	Returns the authenticating user's followers, each with current status inline.
        	They are ordered by the order in which they joined Twitter, 100 at a time.
        	(Note that the result set isn't guaranteed to be 100 every time, as suspended users will be filtered out.) 

        	Use the page option to access earlier followers.

        	Note: The previously documented page-based pagination mechanism is still in production, but please migrate to cursor-based pagination for increase reliability and performance.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Optional. The ID or screen name of the user for whom to request a list of followers. 
        		user_id - Optional. Specfies the ID of the user for whom to return the list of followers. Helpful for disambiguating when a valid user ID is also a valid screen name.
        		screen_name - Optional. Specfies the screen name of the user for whom to return the list of followers. Helpful for disambiguating when a valid screen name is also a user ID.
        		page - (BEING DEPRECATED) Optional. Specifies the page to retrieve.		
        		cursor - Optional. Breaks the results into pages. A single page contains 100 users. This is recommended for users who are following many users. Provide a value of  -1 to begin paging. Provide values as returned to in the response body's next_cursor and previous_cursor attributes to page back and forth in the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = ""
            if id is not None:
                apiURL = "http://api.twitter.com/%d/statuses/followers/%s.json" % (version, id)
            if user_id is not None:
                apiURL = "http://api.twitter.com/%d/statuses/followers.json?user_id=%s" % (version, `user_id`)
            if screen_name is not None:
                apiURL = "http://api.twitter.com/%d/statuses/followers.json?screen_name=%s" % (version, screen_name)
            try:
                if page is not None:
                    return simplejson.load(self.opener.open(apiURL + "&page=%s" % page))
                else:
                    return simplejson.load(self.opener.open(apiURL + "&cursor=%s" % cursor))
            except HTTPError, e:
                raise mtweetsError("getFollowersStatus() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("getFollowersStatus() requires you to be authenticated.")

    
    

    def endSession(self, version = None):
        """endSession()

        	Ends the session of the authenticating user, returning a null cookie. 
        	Use this method to sign users out of client-facing applications (widgets, etc).

        	Parameters:
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                self.opener.open("http://api.twitter.com/%d/account/end_session.json" % version, "")
                self.authenticated = False
            except HTTPError, e:
                raise mtweetsError("endSession failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("You can't end a session when you're not authenticated to begin with.")

    def getDirectMessages(self, since_id = None, max_id = None, count = None, page = "1", version = None):
        """getDirectMessages(since_id = None, max_id = None, count = None, page = "1")

        	Returns a list of the 20 most recent direct messages sent to the authenticating user. 

        	Parameters:
        		since_id - Optional.  Returns only statuses with an ID greater than (that is, more recent than) the specified ID.
        		max_id - Optional.  Returns only statuses with an ID less than (that is, older than) or equal to the specified ID. 
        		count - Optional.  Specifies the number of statuses to retrieve. May not be greater than 200.  
        		page - Optional. Specifies the page of results to retrieve. Note: there are pagination limits.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = "http://api.twitter.com/%d/direct_messages.json?page=%s" % (version, `page`)
            if since_id is not None:
                apiURL += "&since_id=%s" % `since_id`
            if max_id is not None:
                apiURL += "&max_id=%s" % `max_id`
            if count is not None:
                apiURL += "&count=%s" % `count`

            try:
                return simplejson.load(self.opener.open(apiURL))
            except HTTPError, e:
                raise mtweetsError("getDirectMessages() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("getDirectMessages() requires you to be authenticated.")

    def getSentMessages(self, since_id = None, max_id = None, count = None, page = "1", version = None):
        """getSentMessages(since_id = None, max_id = None, count = None, page = "1")

        	Returns a list of the 20 most recent direct messages sent by the authenticating user.

        	Parameters:
        		since_id - Optional.  Returns only statuses with an ID greater than (that is, more recent than) the specified ID.
        		max_id - Optional.  Returns only statuses with an ID less than (that is, older than) or equal to the specified ID. 
        		count - Optional.  Specifies the number of statuses to retrieve. May not be greater than 200.  
        		page - Optional. Specifies the page of results to retrieve. Note: there are pagination limits.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = "http://api.twitter.com/%d/direct_messages/sent.json?page=%s" % (version, `page`)
            if since_id is not None:
                apiURL += "&since_id=%s" % `since_id`
            if max_id is not None:
                apiURL += "&max_id=%s" % `max_id`
            if count is not None:
                apiURL += "&count=%s" % `count`

            try:
                return simplejson.load(self.opener.open(apiURL))
            except HTTPError, e:
                raise mtweetsError("getSentMessages() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("getSentMessages() requires you to be authenticated.")

    def sendDirectMessage(self, user, text, version = None):
        """sendDirectMessage(user, text)

        	Sends a new direct message to the specified user from the authenticating user. Requires both the user and text parameters. 
        	Returns the sent message in the requested format when successful.

        	Parameters:
        		user - Required. The ID or screen name of the recipient user.
        		text - Required. The text of your direct message. Be sure to keep it under 140 characters.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            if len(list(text)) < 140:
                try:
                    return self.opener.open("http://api.twitter.com/%d/direct_messages/new.json" % version, urllib.urlencode({"user": user, "text": text}))
                except HTTPError, e:
                    raise mtweetsError("sendDirectMessage() failed with a %s error code." % `e.code`, e.code)
            else:
                raise mtweetsError("Your message must not be longer than 140 characters")
        else:
            raise AuthError("You must be authenticated to send a new direct message.")

    def destroyDirectMessage(self, id, version = None):
        """destroyDirectMessage(id)

        	Destroys the direct message specified in the required ID parameter.
        	The authenticating user must be the recipient of the specified direct message.

        	Parameters:
        		id - Required. The ID of the direct message to destroy.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return self.opener.open("http://api.twitter.com/%d/direct_messages/destroy/%s.json" % (version, id), "")
            except HTTPError, e:
                raise mtweetsError("destroyDirectMessage() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("You must be authenticated to destroy a direct message.")

    def createFriendship(self, id = None, user_id = None, screen_name = None, follow = "false", version = None):
        """createFriendship(id = None, user_id = None, screen_name = None, follow = "false")

        	Allows the authenticating users to follow the user specified in the ID parameter.
        	Returns the befriended user in the requested format when successful. Returns a
        	string describing the failure condition when unsuccessful. If you are already
        	friends with the user an HTTP 403 will be returned.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Required. The ID or screen name of the user to befriend.
        		user_id - Required. Specfies the ID of the user to befriend. Helpful for disambiguating when a valid user ID is also a valid screen name. 
        		screen_name - Required. Specfies the screen name of the user to befriend. Helpful for disambiguating when a valid screen name is also a user ID. 
        		follow - Optional. Enable notifications for the target user in addition to becoming friends. 
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = ""
            if user_id is not None:
                apiURL = "user_id=%s&follow=%s" %(`user_id`, follow)
            if screen_name is not None:
                apiURL = "screen_name=%s&follow=%s" %(screen_name, follow)
            try:
                if id is not None:
                    return simplejson.load(self.opener.open("http://api.twitter.com/%d/friendships/create/%s.json" % (version, id), "?follow=%s" % follow))
                else:
                    return simplejson.load(self.opener.open("http://api.twitter.com/%d/friendships/create.json" % version, apiURL))
            except HTTPError, e:
                # Rate limiting is done differently here for API reasons...
                if e.code == 403:
                    raise APILimit("You've hit the update limit for this method. Try again in 24 hours.")
                raise mtweetsError("createFriendship() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("createFriendship() requires you to be authenticated.")

    def destroyFriendship(self, id = None, user_id = None, screen_name = None, version = None):
        """destroyFriendship(id = None, user_id = None, screen_name = None)

        	Allows the authenticating users to unfollow the user specified in the ID parameter.  
        	Returns the unfollowed user in the requested format when successful.  Returns a string describing the failure condition when unsuccessful.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Required. The ID or screen name of the user to unfollow. 
        		user_id - Required. Specfies the ID of the user to unfollow. Helpful for disambiguating when a valid user ID is also a valid screen name. 
        		screen_name - Required. Specfies the screen name of the user to unfollow. Helpful for disambiguating when a valid screen name is also a user ID.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = ""
            if user_id is not None:
                apiURL = "user_id=%s" % `user_id`
            if screen_name is not None:
                apiURL = "screen_name=%s" % screen_name
            try:
                if id is not None:
                    return simplejson.load(self.opener.open("http://api.twitter.com/%d/friendships/destroy/%s.json" % (version, `id`), "lol=1")) # Random string hack for POST reasons ;P
                else:
                    return simplejson.load(self.opener.open("http://api.twitter.com/%d/friendships/destroy.json" % version, apiURL))
            except HTTPError, e:
                raise mtweetsError("destroyFriendship() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("destroyFriendship() requires you to be authenticated.")

    def checkIfFriendshipExists(self, user_a, user_b, version = None):
        """checkIfFriendshipExists(user_a, user_b)

        	Tests for the existence of friendship between two users.
        	Will return true if user_a follows user_b; otherwise, it'll return false.

        	Parameters:
        		user_a - Required. The ID or screen_name of the subject user.
        		user_b - Required. The ID or screen_name of the user to test for following.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                friendshipURL = "http://api.twitter.com/%d/friendships/exists.json?%s" % (version, urllib.urlencode({"user_a": user_a, "user_b": user_b}))
                return simplejson.load(self.opener.open(friendshipURL))
            except HTTPError, e:
                raise mtweetsError("checkIfFriendshipExists() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("checkIfFriendshipExists(), oddly, requires that you be authenticated.")

    def showFriendship(self, source_id = None, source_screen_name = None, target_id = None, target_screen_name = None, version = None):
        """showFriendship(source_id, source_screen_name, target_id, target_screen_name)

        	Returns detailed information about the relationship between two users. 

        	Parameters:
        		** Note: One of the following is required if the request is unauthenticated
        		source_id - The user_id of the subject user.
        		source_screen_name - The screen_name of the subject user.

        		** Note: One of the following is required at all times
        		target_id - The user_id of the target user.
        		target_screen_name - The screen_name of the target user.

        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        apiURL = "http://api.twitter.com/%d/friendships/show.json?lol=1" % version # Another quick hack, look away if you want. :D
        if source_id is not None:
            apiURL += "&source_id=%s" % `source_id`
        if source_screen_name is not None:
            apiURL += "&source_screen_name=%s" % source_screen_name
        if target_id is not None:
            apiURL += "&target_id=%s" % `target_id`
        if target_screen_name is not None:
            apiURL += "&target_screen_name=%s" % target_screen_name
        try:
            if self.authenticated is True:
                return simplejson.load(self.opener.open(apiURL))
            else:
                return simplejson.load(self.opener.open(apiURL))
        except HTTPError, e:
            # Catch this for now
            if e.code == 403:
                raise AuthError("You're unauthenticated, and forgot to pass a source for this method. Try again!")
            raise mtweetsError("showFriendship() failed with a %s error code." % `e.code`, e.code)

    def updateDeliveryDevice(self, device_name = "none", version = None):
        """updateDeliveryDevice(device_name = "none")

        	Sets which device Twitter delivers updates to for the authenticating user.
        	Sending "none" as the device parameter will disable IM or SMS updates. (Simply calling .updateDeliveryService() also accomplishes this)

        	Parameters:
        		device - Required. Must be one of: sms, im, none.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return self.opener.open("http://api.twitter.com/%d/account/update_delivery_device.json?" % version, urllib.urlencode({"device": self.unicode2utf8(device_name)}))
            except HTTPError, e:
                raise mtweetsError("updateDeliveryDevice() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("updateDeliveryDevice() requires you to be authenticated.")

    def updateProfileColors(self, 
                            profile_background_color = None, 
                            profile_text_color = None, 
                            profile_link_color = None, 
                            profile_sidebar_fill_color = None, 
                            profile_sidebar_border_color = None, 
                            version = None):
        """updateProfileColors()

        	Sets one or more hex values that control the color scheme of the authenticating user's profile page on api.twitter.com.

        	Parameters:
        		** Note: One or more of the following parameters must be present. Each parameter's value must
        		be a valid hexidecimal value, and may be either three or six characters (ex: #fff or #ffffff).

        		profile_background_color - Optional.
        		profile_text_color - Optional.
        		profile_link_color - Optional.
        		profile_sidebar_fill_color - Optional.
        		profile_sidebar_border_color - Optional.

        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        if self.authenticated is True:
            updateProfileColorsQueryString = "?lol=2"

            def checkValidColor(str):
                if len(str) != 6:
                    return False
                for c in str:
                    if c not in "1234567890abcdefABCDEF": return False

                return True

            if profile_background_color is not None:
                if checkValidColor(profile_background_color):
                    updateProfileColorsQueryString += "profile_background_color=" + profile_background_color
                else:
                    raise mtweetsError("Invalid background color. Try an hexadecimal 6 digit number.")
            if profile_text_color is not None:
                if checkValidColor(profile_text_color):
                    updateProfileColorsQueryString += "profile_text_color=" + profile_text_color
                else:
                    raise mtweetsError("Invalid text color. Try an hexadecimal 6 digit number.")
            if profile_link_color is not None:
                if checkValidColor(profile_link_color):
                    updateProfileColorsQueryString += "profile_link_color=" + profile_link_color
                else:
                    raise mtweetsError("Invalid profile link color. Try an hexadecimal 6 digit number.")
            if profile_sidebar_fill_color is not None:
                if checkValidColor(profile_sidebar_fill_color):
                    updateProfileColorsQueryString += "profile_sidebar_fill_color=" + profile_sidebar_fill_color
                else:
                    raise mtweetsError("Invalid sidebar fill color. Try an hexadecimal 6 digit number.")
            if profile_sidebar_border_color is not None:
                if checkValidColor(profile_sidebar_border_color):
                    updateProfileColorsQueryString += "profile_sidebar_border_color=" + profile_sidebar_border_color
                else:
                    raise mtweetsError("Invalid sidebar border color. Try an hexadecimal 6 digit number.")

            try:
                return self.opener.open("http://api.twitter.com/%d/account/update_profile_colors.json?" % version, updateProfileColorsQueryString)
            except HTTPError, e:
                raise mtweetsError("updateProfileColors() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("updateProfileColors() requires you to be authenticated.")

    def updateProfile(self, name = None, email = None, url = None, location = None, description = None, version = None):
        """updateProfile(name = None, email = None, url = None, location = None, description = None)

        	Sets values that users are able to set under the "Account" tab of their settings page. 
        	Only the parameters specified will be updated.

        	Parameters:
        		One or more of the following parameters must be present.  Each parameter's value
        		should be a string.  See the individual parameter descriptions below for further constraints.

        		name - Optional. Maximum of 20 characters.
        		email - Optional. Maximum of 40 characters. Must be a valid email address.
        		url - Optional. Maximum of 100 characters. Will be prepended with "http://" if not present.
        		location - Optional. Maximum of 30 characters. The contents are not normalized or geocoded in any way.
        		description - Optional. Maximum of 160 characters.

        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            useAmpersands = False
            updateProfileQueryString = ""
            if name is not None:
                if len(list(name)) < 20:
                    updateProfileQueryString += "name=" + name
                    useAmpersands = True
                else:
                    raise mtweetsError("Twitter has a character limit of 20 for all usernames. Try again.")
            if email is not None and "@" in email:
                if len(list(email)) < 40:
                    if useAmpersands is True:
                        updateProfileQueryString += "&email=" + email
                    else:
                        updateProfileQueryString += "email=" + email
                        useAmpersands = True
                else:
                    raise mtweetsError("Twitter has a character limit of 40 for all email addresses, and the email address must be valid. Try again.")
            if url is not None:
                if len(list(url)) < 100:
                    if useAmpersands is True:
                        updateProfileQueryString += "&" + urllib.urlencode({"url": self.unicode2utf8(url)})
                    else:
                        updateProfileQueryString += urllib.urlencode({"url": self.unicode2utf8(url)})
                        useAmpersands = True
                else:
                    raise mtweetsError("Twitter has a character limit of 100 for all urls. Try again.")
            if location is not None:
                if len(list(location)) < 30:
                    if useAmpersands is True:
                        updateProfileQueryString += "&" + urllib.urlencode({"location": self.unicode2utf8(location)})
                    else:
                        updateProfileQueryString += urllib.urlencode({"location": self.unicode2utf8(location)})
                        useAmpersands = True
                else:
                    raise mtweetsError("Twitter has a character limit of 30 for all locations. Try again.")
            if description is not None:
                if len(list(description)) < 160:
                    if useAmpersands is True:
                        updateProfileQueryString += "&" + urllib.urlencode({"description": self.unicode2utf8(description)})
                    else:
                        updateProfileQueryString += urllib.urlencode({"description": self.unicode2utf8(description)})
                else:
                    raise mtweetsError("Twitter has a character limit of 160 for all descriptions. Try again.")

            if updateProfileQueryString != "":
                try:
                    return self.opener.open("http://api.twitter.com/%d/account/update_profile.json?" % version, updateProfileQueryString)
                except HTTPError, e:
                    raise mtweetsError("updateProfile() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("updateProfile() requires you to be authenticated.")

    def getFavorites(self, page = "1", version = None):
        """getFavorites(page = "1")

        	Returns the 20 most recent favorite statuses for the authenticating user or user specified by the ID parameter in the requested format.

        	Parameters:
        		page - Optional. Specifies the page of favorites to retrieve.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/favorites.json?page=%s" % (version, `page`)))
            except HTTPError, e:
                raise mtweetsError("getFavorites() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("getFavorites() requires you to be authenticated.")

    def createFavorite(self, id, version = None):
        """createFavorite(id)

        	Favorites the status specified in the ID parameter as the authenticating user. Returns the favorite status when successful.

        	Parameters:
        		id - Required. The ID of the status to favorite.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/favorites/create/%s.json" % (version, `id`), ""))
            except HTTPError, e:
                raise mtweetsError("createFavorite() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("createFavorite() requires you to be authenticated.")

    def destroyFavorite(self, id, version = None):
        """destroyFavorite(id)

        	Un-favorites the status specified in the ID parameter as the authenticating user. Returns the un-favorited status in the requested format when successful.

        	Parameters:
        		id - Required. The ID of the status to un-favorite.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/favorites/destroy/%s.json" % (version, `id`), ""))
            except HTTPError, e:
                raise mtweetsError("destroyFavorite() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("destroyFavorite() requires you to be authenticated.")

    def notificationFollow(self, id = None, user_id = None, screen_name = None, version = None):
        """notificationFollow(id = None, user_id = None, screen_name = None)

        	Enables device notifications for updates from the specified user. Returns the specified user when successful.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Required. The ID or screen name of the user to follow with device updates.
        		user_id - Required. Specfies the ID of the user to follow with device updates. Helpful for disambiguating when a valid user ID is also a valid screen name. 
        		screen_name - Required. Specfies the screen name of the user to follow with device updates. Helpful for disambiguating when a valid screen name is also a user ID. 
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = ""
            if id is not None:
                apiURL = "http://api.twitter.com/%d/notifications/follow/%s.json" % (version, id)
            if user_id is not None:
                apiURL = "http://api.twitter.com/%d/notifications/follow/follow.json?user_id=%s" % (version, `user_id`)
            if screen_name is not None:
                apiURL = "http://api.twitter.com/%d/notifications/follow/follow.json?screen_name=%s" % (version, screen_name)
            try:
                return simplejson.load(self.opener.open(apiURL, ""))
            except HTTPError, e:
                raise mtweetsError("notificationFollow() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("notificationFollow() requires you to be authenticated.")

    def notificationLeave(self, id = None, user_id = None, screen_name = None, version = None):
        """notificationLeave(id = None, user_id = None, screen_name = None)

        	Disables notifications for updates from the specified user to the authenticating user.  Returns the specified user when successful.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Required. The ID or screen name of the user to follow with device updates.
        		user_id - Required. Specfies the ID of the user to follow with device updates. Helpful for disambiguating when a valid user ID is also a valid screen name. 
        		screen_name - Required. Specfies the screen name of the user to follow with device updates. Helpful for disambiguating when a valid screen name is also a user ID. 
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            apiURL = ""
            if id is not None:
                apiURL = "http://api.twitter.com/%d/notifications/leave/%s.json" % (version, id)
            if user_id is not None:
                apiURL = "http://api.twitter.com/%d/notifications/leave/leave.json?user_id=%s" % (version, `user_id`)
            if screen_name is not None:
                apiURL = "http://api.twitter.com/%d/notifications/leave/leave.json?screen_name=%s" % (version, screen_name)
            try:
                return simplejson.load(self.opener.open(apiURL, ""))
            except HTTPError, e:
                raise mtweetsError("notificationLeave() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("notificationLeave() requires you to be authenticated.")

    def getFriendsIDs(self, id = None, user_id = None, screen_name = None, page = None, cursor = "-1", version = None):
        """getFriendsIDs(id = None, user_id = None, screen_name = None, page = None, cursor = "-1")

        	Returns an array of numeric IDs for every user the specified user is following.

        	Note: The previously documented page-based pagination mechanism is still in production, but please migrate to cursor-based pagination for increase reliability and performance.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Required. The ID or screen name of the user to follow with device updates.
        		user_id - Required. Specfies the ID of the user to follow with device updates. Helpful for disambiguating when a valid user ID is also a valid screen name. 
        		screen_name - Required. Specfies the screen name of the user to follow with device updates. Helpful for disambiguating when a valid screen name is also a user ID. 
        		page - (BEING DEPRECATED) Optional. Specifies the page number of the results beginning at 1. A single page contains up to 5000 ids. This is recommended for users with large ID lists. If not provided all ids are returned. (Please note that the result set isn't guaranteed to be 5000 every time as suspended users will be filtered out.)
        		cursor - Optional. Breaks the results into pages. A single page contains 5000 ids. This is recommended for users with large ID lists. Provide a value of -1 to begin paging. Provide values as returned to in the response body's "next_cursor" and "previous_cursor" attributes to page back and forth in the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        apiURL = ""
        breakResults = "cursor=%s" % cursor
        if page is not None:
            breakResults = "page=%s" % page
        if id is not None:
            apiURL = "http://api.twitter.com/%d/friends/ids/%s.json?%s" %(version, id, breakResults)
        if user_id is not None:
            apiURL = "http://api.twitter.com/%d/friends/ids.json?user_id=%s&%s" %(version, `user_id`, breakResults)
        if screen_name is not None:
            apiURL = "http://api.twitter.com/%d/friends/ids.json?screen_name=%s&%s" %(version, screen_name, breakResults)
        try:
            return simplejson.load(self.opener.open(apiURL))
        except HTTPError, e:
            raise mtweetsError("getFriendsIDs() failed with a %s error code." % `e.code`, e.code)

    def getFollowersIDs(self, id = None, user_id = None, screen_name = None, page = None, cursor = "-1", version = None):
        """getFollowersIDs(id = None, user_id = None, screen_name = None, page = None, cursor = "-1")

        	Returns an array of numeric IDs for every user following the specified user.

        	Note: The previously documented page-based pagination mechanism is still in production, but please migrate to cursor-based pagination for increase reliability and performance.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Required. The ID or screen name of the user to follow with device updates.
        		user_id - Required. Specfies the ID of the user to follow with device updates. Helpful for disambiguating when a valid user ID is also a valid screen name. 
        		screen_name - Required. Specfies the screen name of the user to follow with device updates. Helpful for disambiguating when a valid screen name is also a user ID. 
        		page - (BEING DEPRECATED) Optional. Specifies the page number of the results beginning at 1. A single page contains 5000 ids. This is recommended for users with large ID lists. If not provided all ids are returned. (Please note that the result set isn't guaranteed to be 5000 every time as suspended users will be filtered out.)
        		cursor - Optional. Breaks the results into pages. A single page contains 5000 ids. This is recommended for users with large ID lists. Provide a value of -1 to begin paging. Provide values as returned to in the response body's "next_cursor" and "previous_cursor" attributes to page back and forth in the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        apiURL = ""
        breakResults = "cursor=%s" % cursor
        if page is not None:
            breakResults = "page=%s" % page
        if id is not None:
            apiURL = "http://api.twitter.com/%d/followers/ids/%s.json?%s" % (version, `id`, breakResults)
        if user_id is not None:
            apiURL = "http://api.twitter.com/%d/followers/ids.json?user_id=%s&%s" %(version, `user_id`, breakResults)
        if screen_name is not None:
            apiURL = "http://api.twitter.com/%d/followers/ids.json?screen_name=%s&%s" %(version, screen_name, breakResults)
        try:
            return simplejson.load(self.opener.open(apiURL))
        except HTTPError, e:
            raise mtweetsError("getFollowersIDs() failed with a %s error code." % `e.code`, e.code)

    def createBlock(self, id, version = None):
        """createBlock(id)

        	Blocks the user specified in the ID parameter as the authenticating user. Destroys a friendship to the blocked user if it exists. 
        	Returns the blocked user in the requested format when successful.

        	Parameters:
        		id - The ID or screen name of a user to block.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/blocks/create/%s.json" % (version, `id`), ""))
            except HTTPError, e:
                raise mtweetsError("createBlock() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("createBlock() requires you to be authenticated.")

    def destroyBlock(self, id, version = None):
        """destroyBlock(id)

        	Un-blocks the user specified in the ID parameter for the authenticating user.
        	Returns the un-blocked user in the requested format when successful.

        	Parameters:
        		id - Required. The ID or screen_name of the user to un-block
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/blocks/destroy/%s.json" % (version, `id`), ""))
            except HTTPError, e:
                raise mtweetsError("destroyBlock() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("destroyBlock() requires you to be authenticated.")

    def checkIfBlockExists(self, id = None, user_id = None, screen_name = None, version = None):
        """checkIfBlockExists(id = None, user_id = None, screen_name = None)

        	Returns if the authenticating user is blocking a target user. Will return the blocked user's object if a block exists, and 
        	error with an HTTP 404 response code otherwise.

        	Parameters:
        		** Note: One of the following is required. (id, user_id, screen_name)
        		id - Optional. The ID or screen_name of the potentially blocked user.
        		user_id - Optional. Specfies the ID of the potentially blocked user. Helpful for disambiguating when a valid user ID is also a valid screen name.
        		screen_name - Optional. Specfies the screen name of the potentially blocked user. Helpful for disambiguating when a valid screen name is also a user ID.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        apiURL = ""
        if id is not None:
            apiURL = "http://api.twitter.com/%d/blocks/exists/%s.json" % (version, `id`)
        if user_id is not None:
            apiURL = "http://api.twitter.com/%d/blocks/exists.json?user_id=%s" % (version, `user_id`)
        if screen_name is not None:
            apiURL = "http://api.twitter.com/%d/blocks/exists.json?screen_name=%s" % (version, screen_name)
        try:
            return simplejson.load(self.opener.open(apiURL))
        except HTTPError, e:
            raise mtweetsError("checkIfBlockExists() failed with a %s error code." % `e.code`, e.code)

    def getBlocking(self, page = "1", version = None):
        """getBlocking(page = "1")

        	Returns an array of user objects that the authenticating user is blocking.

        	Parameters:
        		page - Optional. Specifies the page number of the results beginning at 1. A single page contains 20 ids.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/blocks/blocking.json?page=%s" % (version, `page`)))
            except HTTPError, e:
                raise mtweetsError("getBlocking() failed with a %s error code." %	`e.code`, e.code)
        else:
            raise AuthError("getBlocking() requires you to be authenticated")

    def getBlockedIDs(self, version = None):
        """getBlockedIDs()

        	Returns an array of numeric user ids the authenticating user is blocking.

        	Parameters:
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/blocks/blocking/ids.json" % version))
            except HTTPError, e:
                raise mtweetsError("getBlockedIDs() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("getBlockedIDs() requires you to be authenticated.")

    def searchTwitter(self, search_query, **kwargs):
        """searchTwitter(search_query, **kwargs)

        	Returns tweets that match a specified query.

        	Parameters:
        		callback - Optional. Only available for JSON format. If supplied, the response will use the JSONP format with a callback of the given name.
        		lang - Optional. Restricts tweets to the given language, given by an ISO 639-1 code.
        		locale - Optional. Language of the query you're sending (only ja is currently effective). Intended for language-specific clients; default should work in most cases.
        		rpp - Optional. The number of tweets to return per page, up to a max of 100.
        		page - Optional. The page number (starting at 1) to return, up to a max of roughly 1500 results (based on rpp * page. Note: there are pagination limits.)
        		since_id - Optional. Returns tweets with status ids greater than the given id.
        		geocode - Optional. Returns tweets by users located within a given radius of the given latitude/longitude, where the user's location is taken from their Twitter profile. The parameter value is specified by "latitide,longitude,radius", where radius units must be specified as either "mi" (miles) or "km" (kilometers). Note that you cannot use the near operator via the API to geocode arbitrary locations; however you can use this geocode parameter to search near geocodes directly.
        		show_user - Optional. When true, prepends "<user>:" to the beginning of the tweet. This is useful for readers that do not display Atom's author field. The default is false. 

        	Usage Notes:
        		Queries are limited 140 URL encoded characters.
        		Some users may be absent from search results.
        		The since_id parameter will be removed from the next_page element as it is not supported for pagination. If since_id is removed a warning will be added to alert you.
        		This method will return an HTTP 404 error if since_id is used and is too old to be in the search index.

        	Applications must have a meaningful and unique User Agent when using this method. 
        	An HTTP Referrer is expected but not required. Search traffic that does not include a User Agent will be rate limited to fewer API calls per hour than 
        	applications including a User Agent string. You can set your custom UA headers by passing it as a respective argument to the setup() method.
        """
        searchURL = self.constructApiURL("http://search.twitter.com/search.json", kwargs) + "&" + urllib.urlencode({"q": self.unicode2utf8(search_query)})
        try:
            return simplejson.load(self.opener.open(searchURL))
        except HTTPError, e:
            raise mtweetsError("getSearchTimeline() failed with a %s error code." % `e.code`, e.code)

    def getCurrentTrends(self, excludeHashTags = False, version = None):
        """getCurrentTrends(excludeHashTags = False, version = None)

        	Returns the current top 10 trending topics on Twitter.  The response includes the time of the request, the name of each trending topic, and the query used 
        	on Twitter Search results page for that topic.

        	Parameters:
        		excludeHashTags - Optional. Setting this equal to hashtags will remove all hashtags from the trends list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        apiURL = "http://api.twitter.com/%d/trends/current.json" % version
        if excludeHashTags is True:
            apiURL += "?exclude=hashtags"
        try:
            return simplejson.load(self.opener.open(apiURL))
        except HTTPError, e:
            raise mtweetsError("getCurrentTrends() failed with a %s error code." % `e.code`, e.code)

    def getDailyTrends(self, date = None, exclude = False, version = None):
        """getDailyTrends(date = None, exclude = False, version = None)

        	Returns the top 20 trending topics for each hour in a given day.

        	Parameters:
        		date - Optional. Permits specifying a start date for the report. The date should be formatted YYYY-MM-DD.
        		exclude - Optional. Setting this equal to hashtags will remove all hashtags from the trends list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        apiURL = "http://api.twitter.com/%d/trends/daily.json" % version
        questionMarkUsed = False
        if date is not None:
            apiURL += "?date=%s" % date
            questionMarkUsed = True
        if exclude is True:
            if questionMarkUsed is True:
                apiURL += "&exclude=hashtags"
            else:
                apiURL += "?exclude=hashtags"
        try:
            return simplejson.load(self.opener.open(apiURL))
        except HTTPError, e:
            raise mtweetsError("getDailyTrends() failed with a %s error code." % `e.code`, e.code)

    def getWeeklyTrends(self, date = None, exclude = False):
        """getWeeklyTrends(date = None, exclude = False)

        	Returns the top 30 trending topics for each day in a given week.

        	Parameters:
        		date - Optional. Permits specifying a start date for the report. The date should be formatted YYYY-MM-DD.
        		exclude - Optional. Setting this equal to hashtags will remove all hashtags from the trends list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        apiURL = "http://api.twitter.com/%d/trends/daily.json" % version
        questionMarkUsed = False
        if date is not None:
            apiURL += "?date=%s" % date
            questionMarkUsed = True
        if exclude is True:
            if questionMarkUsed is True:
                apiURL += "&exclude=hashtags"
            else:
                apiURL += "?exclude=hashtags"
        try:
            return simplejson.load(self.opener.open(apiURL))
        except HTTPError, e:
            raise mtweetsError("getWeeklyTrends() failed with a %s error code." % `e.code`, e.code)

    def getSavedSearches(self, version = None):
        """getSavedSearches()

        	Returns the authenticated user's saved search queries.

        	Parameters:
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/saved_searches.json" % version))
            except HTTPError, e:
                raise mtweetsError("getSavedSearches() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("getSavedSearches() requires you to be authenticated.")

    def showSavedSearch(self, id, version = None):
        """showSavedSearch(id)

        	Retrieve the data for a saved search owned by the authenticating user specified by the given id.

        	Parameters:
        		id - Required. The id of the saved search to be retrieved.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/saved_searches/show/%s.json" % (version, `id`)))
            except HTTPError, e:
                raise mtweetsError("showSavedSearch() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("showSavedSearch() requires you to be authenticated.")

    def createSavedSearch(self, query, version = None):
        """createSavedSearch(query)

        	Creates a saved search for the authenticated user.

        	Parameters:
        		query - Required. The query of the search the user would like to save.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/saved_searches/create.json?query=%s" % (version, query), ""))
            except HTTPError, e:
                raise mtweetsError("createSavedSearch() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("createSavedSearch() requires you to be authenticated.")

    def destroySavedSearch(self, id, version = None):
        """ destroySavedSearch(id)

        	Destroys a saved search for the authenticated user.
        	The search specified by id must be owned by the authenticating user.

        	Parameters:
        		id - Required. The id of the saved search to be deleted.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/saved_searches/destroy/%s.json" % (version, `id`), ""))
            except HTTPError, e:
                raise mtweetsError("destroySavedSearch() failed with a %s error code." % `e.code`, e.code)
        else:
            raise AuthError("destroySavedSearch() requires you to be authenticated.")

    def createList(self, name, mode = "public", description = "", version = None):
        """ createList(self, name, mode, description, version)

        	Creates a new list for the currently authenticated user. (Note: This may encounter issues if you authenticate with an email; try username (screen name) instead).

        	Parameters:
        		name - Required. The name for the new list.
        		description - Optional, in the sense that you can leave it blank if you don't want one. ;)
        		mode - Optional. This is a string indicating "public" or "private", defaults to "public".
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/lists.json" % (version, self.username), 
                                                        urllib.urlencode({"name": name, "mode": mode, "description": description})))
            except HTTPError, e:
                raise mtweetsError("createList() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("createList() requires you to be authenticated.")

    def updateList(self, list_id, name, mode = "public", description = "", version = None):
        """ updateList(self, list_id, name, mode, description, version)

        	Updates an existing list for the authenticating user. (Note: This may encounter issues if you authenticate with an email; try username (screen name) instead).
        	This method is a bit cumbersome for the time being; I'd personally avoid using it unless you're positive you know what you're doing. Twitter should really look
        	at this...

        	Parameters:
        		list_id - Required. The name of the list (this gets turned into a slug - e.g, "Huck Hound" becomes "huck-hound").
        		name - Required. The name of the list, possibly for renaming or such.
        		description - Optional, in the sense that you can leave it blank if you don't want one. ;)
        		mode - Optional. This is a string indicating "public" or "private", defaults to "public".
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/lists/%s.json" % (version, self.username, list_id), 
                                                        urllib.urlencode({"name": name, "mode": mode, "description": description})))
            except HTTPError, e:
                raise mtweetsError("updateList() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("updateList() requires you to be authenticated.")

    def showLists(self, version = None):
        """ showLists(self, version)

        	Show all the lists for the currently authenticated user (i.e, they own these lists).
        	(Note: This may encounter issues if you authenticate with an email; try username (screen name) instead).

        	Parameters:
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/lists.json" % (version, self.username)))
            except HTTPError, e:
                raise mtweetsError("showLists() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("showLists() requires you to be authenticated.")

    def getListMemberships(self, version = None):
        """ getListMemberships(self, version)

        	Get all the lists for the currently authenticated user (i.e, they're on all the lists that are returned, the lists belong to other people)
        	(Note: This may encounter issues if you authenticate with an email; try username (screen name) instead).

        	Parameters:
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/lists/followers.json" % (version, self.username)))
            except HTTPError, e:
                raise mtweetsError("getLists() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("getLists() requires you to be authenticated.")

    def deleteList(self, list_id, version = None):
        """ deleteList(self, list_id, version)

        	Deletes a list for the authenticating user. 

        	Parameters:
        		list_id - Required. The name of the list to delete - this gets turned into a slug, so you can pass it as that, or hope the transformation works out alright.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/lists/%s.json" % (version, self.username, list_id), "_method=DELETE"))
            except HTTPError, e:
                raise mtweetsError("deleteList() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("deleteList() requires you to be authenticated.")

    def getListTimeline(self, list_id, cursor = "-1", version = None, **kwargs):
        """ getListTimeline(self, list_id, cursor, version, **kwargs)

        	Retrieves a timeline representing everyone in the list specified.

        	Parameters:
        		list_id - Required. The name of the list to get a timeline for - this gets turned into a slug, so you can pass it as that, or hope the transformation works out alright.
        		since_id - Optional.  Returns only statuses with an ID greater than (that is, more recent than) the specified ID.
        		max_id - Optional.  Returns only statuses with an ID less than (that is, older than) or equal to the specified ID. 
        		count - Optional.  Specifies the number of statuses to retrieve. May not be greater than 200.
        		cursor - Optional. Breaks the results into pages. Provide a value of -1 to begin paging. 
        			Provide values returned in the response's "next_cursor" and "previous_cursor" attributes to page back and forth in the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            baseURL = self.constructApiURL("http://api.twitter.com/%d/%s/lists/%s/statuses.json" % (version, self.username, list_id), kwargs)
            return simplejson.load(self.opener.open(baseURL + "&cursor=%s" % cursor))
        except HTTPError, e:
            if e.code == 404:
                raise AuthError("It seems the list you're trying to access is private/protected, and you don't have access. Are you authenticated and allowed?")
            raise mtweetsError("getListTimeline() failed with a %d error code." % e.code, e.code)

    def getSpecificList(self, list_id, version = None):
        """ getSpecificList(self, list_id, version)

        	Retrieve a specific list - this only requires authentication if the list you're requesting is protected/private (if it is, you need to have access as well).

        	Parameters:
        		list_id - Required. The name of the list to get - this gets turned into a slug, so you can pass it as that, or hope the transformation works out alright.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            if self.authenticated is True:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/lists/%s/statuses.json" % (version, self.username, list_id)))
            else:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/lists/%s/statuses.json" % (version, self.username, list_id)))
        except HTTPError, e:
            if e.code == 404:
                raise AuthError("It seems the list you're trying to access is private/protected, and you don't have access. Are you authenticated and allowed?")
            raise mtweetsError("getSpecificList() failed with a %d error code." % e.code, e.code)

    def addListMember(self, list_id, version = None):
        """ addListMember(self, list_id, id, version)

        	Adds a new Member (the passed in id) to the specified list.

        	Parameters:
        		list_id - Required. The slug of the list to add the new member to.
        		id - Required. The ID of the user that's being added to the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/members.json" % (version, self.username, list_id), "id=%s" % `id`))
            except HTTPError, e:
                raise mtweetsError("addListMember() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("addListMember requires you to be authenticated.")

    def getListMembers(self, list_id, version = None):
        """ getListMembers(self, list_id, version = None)

        	Show all members of a specified list. This method requires authentication if the list is private/protected.

        	Parameters:
        		list_id - Required. The slug of the list to retrieve members for.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            if self.authenticated is True:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/members.json" % (version, self.username, list_id)))
            else:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/members.json" % (version, self.username, list_id)))
        except HTTPError, e:
            raise mtweetsError("getListMembers() failed with a %d error code." % e.code, e.code)

    def removeListMember(self, list_id, id, version = None):
        """ removeListMember(self, list_id, id, version)

        	Remove the specified user (id) from the specified list (list_id). Requires you to be authenticated and in control of the list in question.

        	Parameters:
        		list_id - Required. The slug of the list to remove the specified user from.
        		id - Required. The ID of the user that's being added to the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/members.json" % (version, self.username, list_id), "_method=DELETE&id=%s" % `id`))
            except HTTPError, e:
                raise mtweetsError("getListMembers() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("removeListMember() requires you to be authenticated.")

    def isListMember(self, list_id, id, version = None):
        """ isListMember(self, list_id, id, version)

        	Check if a specified user (id) is a member of the list in question (list_id).

        	**Note: This method may not work for private/protected lists, unless you're authenticated and have access to those lists.

        	Parameters:
        		list_id - Required. The slug of the list to check against.
        		id - Required. The ID of the user being checked in the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            if self.authenticated is True:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/members/%s.json" % (version, self.username, list_id, `id`)))
            else:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/members/%s.json" % (version, self.username, list_id, `id`)))
        except HTTPError, e:
            raise mtweetsError("isListMember() failed with a %d error code." % e.code, e.code)

    def subscribeToList(self, list_id, version):
        """ subscribeToList(self, list_id, version)

        	Subscribe the authenticated user to the list provided (must be public).

        	Parameters:
        		list_id - Required. The list to subscribe to.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/following.json" % (version, self.username, list_id), ""))
            except HTTPError, e:
                raise mtweetsError("subscribeToList() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("subscribeToList() requires you to be authenticated.")

    def unsubscribeFromList(self, list_id, version):
        """ unsubscribeFromList(self, list_id, version)

        	Unsubscribe the authenticated user from the list in question (must be public).

        	Parameters:
        		list_id - Required. The list to unsubscribe from.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        if self.authenticated is True:
            try:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/following.json" % (version, self.username, list_id), "_method=DELETE"))
            except HTTPError, e:
                raise mtweetsError("unsubscribeFromList() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("unsubscribeFromList() requires you to be authenticated.")

    def isListSubscriber(self, list_id, id, version = None):
        """ isListSubscriber(self, list_id, id, version)

        	Check if a specified user (id) is a subscriber of the list in question (list_id).

        	**Note: This method may not work for private/protected lists, unless you're authenticated and have access to those lists.

        	Parameters:
        		list_id - Required. The slug of the list to check against.
        		id - Required. The ID of the user being checked in the list.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            if self.authenticated is True:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/following/%s.json" % (version, self.username, list_id, `id`)))
            else:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/%s/%s/following/%s.json" % (version, self.username, list_id, `id`)))
        except HTTPError, e:
            raise mtweetsError("isListMember() failed with a %d error code." % e.code, e.code)

    def availableTrends(self, latitude = None, longitude = None, version = None):
        """ availableTrends(latitude, longitude, version):

        	Gets all available trends, optionally filtering by geolocation based stuff.

        	Note: If you choose to pass a latitude/longitude, keep in mind that you have to pass both - one won't work by itself. ;P

        	Parameters:
        		latitude (string) - Optional. A latitude to sort by.
        		longitude (string) - Optional. A longitude to sort by.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            if latitude is not None and longitude is not None:
                return simplejson.load(self.opener.open("http://api.twitter.com/%d/trends/available.json?latitude=%s&longitude=%s" % (version, latitude, longitude)))
            return simplejson.load(self.opener.open("http://api.twitter.com/%d/trends/available.json" % version))
        except HTTPError, e:
            raise mtweetsError("availableTrends() failed with a %d error code." % e.code, e.code)

    def trendsByLocation(self, woeid, version = None):
        """ trendsByLocation(woeid, version):

        	Gets all available trends, filtering by geolocation (woeid - see http://developer.yahoo.com/geo/geoplanet/guide/concepts.html).

        	Note: If you choose to pass a latitude/longitude, keep in mind that you have to pass both - one won't work by itself. ;P

        	Parameters:
        		woeid (string) - Required. WoeID of the area you're searching in.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        try:
            return simplejson.load(self.opener.open("http://api.twitter.com/%d/trends/%s.json" % (version, woeid)))
        except HTTPError, e:
            raise mtweetsError("trendsByLocation() failed with a %d error code." % e.code, e.code)

    # The following methods are apart from the other Account methods, because they rely on a whole multipart-data posting function set.
    def updateProfileBackgroundImage(self, filename, tile="true", version = None):
        """ updateProfileBackgroundImage(filename, tile="true")

        	Updates the authenticating user's profile background image.

        	Parameters:
        		image - Required. Must be a valid GIF, JPG, or PNG image of less than 800 kilobytes in size. Images with width larger than 2048 pixels will be forceably scaled down.
        		tile - Optional (defaults to true). If set to true the background image will be displayed tiled. The image will not be tiled otherwise. 
        		** Note: It's sad, but when using this method, pass the tile value as a string, e.g tile="false"
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                files = [("image", filename, open(filename, 'rb').read())]
                fields = []
                content_type, body = self.encode_multipart_formdata(fields, files)
                headers = {'Content-Type': content_type, 'Content-Length': str(len(body))}
                r = urllib2.Request("http://api.twitter.com/%d/account/update_profile_background_image.json?tile=%s" % (version, tile), body, headers)
                return self.opener.open(r).read()
            except HTTPError, e:
                raise mtweetsError("updateProfileBackgroundImage() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("You realize you need to be authenticated to change a background image, right?")

    def updateProfileImage(self, filename, version = None):
        """ updateProfileImage(filename)

        	Updates the authenticating user's profile image (avatar).

        	Parameters:
        		image - Required. Must be a valid GIF, JPG, or PNG image of less than 700 kilobytes in size. Images with width larger than 500 pixels will be scaled down.
        		version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if self.authenticated is True:
            try:
                files = [("image", filename, open(filename, 'rb').read())]
                fields = []
                content_type, body = self.encode_multipart_formdata(fields, files)
                headers = {'Content-Type': content_type, 'Content-Length': str(len(body))}
                r = urllib2.Request("http://api.twitter.com/%d/account/update_profile_image.json" % version, body, headers)
                return self.opener.open(r).read()
            except HTTPError, e:
                raise mtweetsError("updateProfileImage() failed with a %d error code." % e.code, e.code)
        else:
            raise AuthError("You realize you need to be authenticated to change a profile image, right?")

    def encode_multipart_formdata(self, fields, files):
        BOUNDARY = mimetools.choose_boundary()
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self.get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def get_content_type(self, filename):
        """ get_content_type(self, filename)

        	Exactly what you think it does. :D
        """
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def unicode2utf8(self, text):
        try:
            if isinstance(text, unicode):
                text = text.encode('utf-8')
        except:
            pass
        return text
