#!/usr/bin/python

"""mtweets - Easy Twitter utilities in Python

mtweets is an up-to-date library for Python that wraps the Twitter API.
Other Python Twitter libraries seem to have fallen a bit behind, and
Twitter's API has evolved a bit. Here's hoping this helps.

Please review the online twitter docs for concepts used by twitter:

    http://developer.twitter.com/doc

like as Tweet entities, and how use each parameter
"""

__author__ = "Luis C. Cruz <carlitos.kyo@gmail.com>"
__version__ = "0.1"

import urllib, mimetypes, mimetools

from urlparse import urlparse

from mtweets.utils import AuthError
from mtweets.utils import RequestError
from mtweets.utils import TwitterClient
from mtweets.utils import simple_decorator as _simple_decorator
from mtweets.utils import authentication_required as _authentication_required

class API(TwitterClient):
    """ This handle simple authentication flow.
    
    convention for methods: 'resource'_'action'
    ej:
        API.public_timeline_get
        API.direct_message_create
    
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
            
    ############################################################################
    ## Timeline methods
    ############################################################################
    
    @_simple_decorator
    def public_timeline_get(self, version=None, **kwargs):
        """public_timeline_get()

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
        
        if len(kwargs) > 0:
            url = "http://api.twitter.com/%d/statuses/public_timeline.json?%s"%(version, urllib.urlencode(kwargs))
        else:
            url = "http://api.twitter.com/%d/statuses/public_timeline.json"%version
            
        return self.opener.open(url)
        
    @_authentication_required
    def home_timeline_get(self, version=None, **kwargs):
        """home_timeline_get()

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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/home_timeline.json"%version, kwargs)      
    
    @_authentication_required
    def friends_timeline_get(self, version=None, **kwargs):
        """friends_timeline_get()

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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/friends_timeline.json"%version, kwargs)
        
    @_simple_decorator
    def user_timeline_get(self, version=None, **kwargs): 
        """user_timeline_get()

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
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/statuses/user_timeline.json"%version, kwargs)
    
    @_authentication_required
    def mentions_get(self, version=None, **kwargs):
        """mentions_get()

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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/mentions.json"%version, kwargs)
        
    @_authentication_required
    def retweeted_of_me_get(self, version=None, **kwargs):
        """retweeted_of_me_get()

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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/retweets_of_me.json"%version, kwargs)
    
    @_authentication_required
    def retweeted_by_me_get(self, version=None, **kwargs):
        """retweeted_by_me_get()

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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/retweeted_by_me.json"%version, kwargs)
                
    @_authentication_required
    def retweeted_to_me_get(self, version=None, **kwargs):
        """retweeted_to_me_get()

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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/retweeted_to_me.json"%version, kwargs)
        
    ############################################################################
    ## Status methods
    ############################################################################
    
    @_simple_decorator
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/show/%d.json"%(version, id), kwargs)
        
    @_authentication_required
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/update.json"%version, kwargs, 'POST')
        
    @_authentication_required
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/destroy/%s.json"%(version, id), kwargs, 'POST')
        
    @_authentication_required    
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/retweet/%s.json"%(version, id), kwargs, 'POST')
        
    @_simple_decorator
    def retweets_get(self, id, version=None, **kwargs):
        """retweets_get(id):
    
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/retweets/%s.json"%(version, id), kwargs)
    
    @_authentication_required
    def retweeted_by_get(self, id, version=None, **kwargs):
        """retweeted_by_get(id):
    
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/%s/retweeted_by.json"%(version, id), kwargs)
    
    @_authentication_required
    def retweeted_by_ids_get(self, id, version=None, **kwargs):
        """retweeted_by_ids_get(id):
    
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/%s/retweeted_by/ids.json"%(version, id), kwargs)
    
    ############################################################################
    ## User methods
    ############################################################################
        
    @_simple_decorator
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
            
        return self.fetch_resource("http://api.twitter.com/%d/users/show.json"%(version), kwargs)
    
    @_authentication_required
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
        if user_id is None and screen_name is None:
            raise RequestError('user_lookup(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        if ids is not None:
            kwargs['user_id'] = ','.join(ids)
        if screen_names is not None:
            kwargs['screen_name'] = ','.join(screen_names)
            
        return self.fetch_resource("http://api.twitter.com/%d/users/lookup.json"%version, kwargs, 'POST')
        
    @_authentication_required
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
        kwargs['q'] = query
        return self.fetch_resource("http://api.twitter.com/%d/users/search.json"%version, kwargs)
        
    @_simple_decorator
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
        return self.fetch_resource("http://api.twitter.com/%d/users/suggestions.json"%version)
    
    @_simple_decorator
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
        return self.fetch_resource("http://api.twitter.com/%d/users/suggestions/%s.json"%(version, slug))
    
    @_simple_decorator
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
        return self.fetch_resource("http://api.twitter.com/%d/users/profile_image/%s.json"%(version, screen_name), kwargs)
    
    @_simple_decorator
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/friends.json"%(version), kwargs)
    
    @_simple_decorator
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
        return self.fetch_resource("http://api.twitter.com/%d/statuses/followers.json"%(version), kwargs)
    
    ############################################################################
    ## Trends methods
    ############################################################################
    
    @_simple_decorator
    def trends_get(self, version=None):
        """trends_get()
               
        Returns the top ten topics that are currently trending on Twitter. The
        response includes the time of the request, the name of each trend, and
        the url to the Twitter Search results page for that topic.

        Parameters:
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.opener.open("http://api.twitter.com/%d/trends.json"%(version))
        
    @_simple_decorator
    def trends_current(self, version=None, **kwargs):
        """trends_current()
        
        Returns the current top 10 trending topics on Twitter. The response
        includes the time of the request, the name of each trending topic, and
        query used on Twitter Search results page for that topic.

        Parameters:
            exclude - Setting this equal to hashtags will remove all hashtags 
                      from the trends list. 
                            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if len(kwargs) > 0:
            url = "http://api.twitter.com/%d/trends/current.json?%s"%(version, urllib.urlencode(kwargs))
        else:
            url = "http://api.twitter.com/%d/trends/current.json"%version                
        return self.opener.open(url)        
    
    @_simple_decorator
    def trends_dialy(self, version=None, **kwargs):
        """trends_dialy()
        
        Returns the top 20 trending topics for each hour in a given day.

        Parameters:
            date - The start date for the report. The date should be formatted
                   YYYY-MM-DD. A 404 error will be thrown if the date is older
                   than the available search index (7-10 days). Dates in the
                   future will be forced to the current date.
          
            exclude - Setting this equal to hashtags will remove all hashtags
                      from the trends list.
                            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if len(kwargs) > 0:
            url = "http://api.twitter.com/%s/trends/daily.json?%s"%(version, urllib.urlencode(kwargs))
        else:
            url = "http://api.twitter.com/%s/trends/daily.json"%version                
        return self.opener.open(url)

    @_simple_decorator
    def trends_weekly(self, version=None, **kwargs):
        """trends_weekly()
        
        Returns the top 30 trending topics for each day in a given week.

        Parameters:
            date - The start date for the report. The date should be formatted
                   YYYY-MM-DD. A 404 error will be thrown if the date is older
                   than the available search index (3-4 weeks). Dates in the
                   future will be forced to the current date.
          
            exclude - Setting this equal to hashtags will remove all hashtags
                      from the trends list.
                            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if len(kwargs) > 0:
            url = "http://api.twitter.com/%d/trends/weekly.json?%s"%(version, urllib.urlencode(kwargs))
        else:
            url = "http://api.twitter.com/%d/trends/weekly.json"%version                
        return self.opener.open(url)
        
    ############################################################################
    ## Local trends methods
    ############################################################################
    
    @_simple_decorator
    def trends_available(self, version=None, **kwargs):
        """trends_available()
        
        Returns the locations that Twitter has trending topic information for.

        The response is an array of "locations" that encode the location's WOEID
        and some other human-readable information such as a canonical name and
        country the location belongs in.

        A WOEID is a Yahoo! Where On Earth ID.

        Parameters:
            lat - If provided with a long parameter the available trend
                  locations will be sorted by distance, nearest to furthest, to
                  the co-ordinate pair. The valid ranges for longitude is -180.0
                  to +180.0 (East is positive) inclusive.
          
            long - If provided with a lat parameter the available trend
                   locations will be sorted by distance, nearest to furthest,
                   to the co-ordinate pair. The valid ranges for longitude is
                   -180.0 to +180.0 (East is positive) inclusive.
                            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if len(kwargs) > 0:
            url = "http://api.twitter.com/%d/trends/available.json?%s"%(version, urllib.urlencode(kwargs))
        else:
            url = "http://api.twitter.com/%d/trends/available.json"%version                
        return self.opener.open(url)
    
    @_simple_decorator
    def trends_woeid_get(self, woeid, version=None):
        """trends_woeid_get(woeid)
        
        Returns the top 10 trending topics for a specific WOEID, if trending
        information is available for it.

        The response is an array of "trend" objects that encode the name of the
        trending topic, the query parameter that can be used to search for the
        topic on Twitter Search, and the Twitter Search URL.

        This information is cached for 5 minutes. Requesting more frequently
        than that will not return any more data, and will count against your
        rate limit usage.

        Parameters:
            woeid - The Yahoo! Where On Earth ID of the location to return
                    trending information for. Global information is available
                    by using 1 as the WOEID. 
                            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.opener.open("http://api.twitter.com/%d/trends/%d.json"%(version, woeid))
    
    ############################################################################
    ## List methods
    ############################################################################
    
    @_authentication_required
    def user_list(self, user, name, version=None, **kwargs):
        """user_list(user, name)
        
        Creates a new list for the authenticated user. Accounts are limited to
        20 lists.
        
        Parameters:
            user - username

            name - The name for the list.
          
            mode - Whether your list is public or private. Values can be public
                   or private. If no mode is specified the list will be public.
          
            description - The description to give the list. 
                    
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['name'] = name
        return self.fetch_resource("http://api.twitter.com/%d/%s/lists.json"%(version, user), kwargs, 'POST')
    
    @_authentication_required
    def user_list_id(self, user, id, version=None, **kwargs):
        """user_list_id(user, id)
        
        Updates the specified list.
        
        Parameters:
            user - username
            
            id - The id or slug of the list.

            name - The name for the list.
          
            mode - Whether your list is public or private. Values can be public
                   or private. If no mode is specified the list will be public.
          
            description - The description to give the list. 
                    
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/%s/lists/%s.json"%(version, user, id), kwargs, 'POST')
            
    @_authentication_required    
    def user_list_get(self, user, version=None, **kwargs):
        """get_user_list(user)
        
        List the lists of the specified user. Private lists will be included if
        the authenticated users is the same as the user who's lists are being
        returned.
        
        Parameters:
            user - twitter username
          
            cursor - Breaks the results into pages. A single page contains 20
                     lists. Provide a value of -1 to begin paging. Provide
                     values as returned in the response body's next_cursor and
                     previous_cursor attributes to page back and forth in the list. 
                    
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/%s/lists.json"%(version, user), kwargs)
    
    @_authentication_required
    def user_list_id_get(self, user, id, version=None, **kwargs):
        """get_user_list_id(user, id)
        
        Show the specified list. Private lists will only be shown if the
        authenticated user owns the specified list.
        
        Parameters:
            user - username

            id - The id or slug of the list.
                    
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/%s/lists/%s.json"%(version, user, id), kwargs)
    
    @_authentication_required
    def user_list_id_delete(self, user, id, version=None, **kwargs):
        """user_list_id_delete(user, id)
        
        Deletes the specified list. Must be owned by the authenticated user.
        
        Parameters:
            user - username
            
            id - The id or slug of the list.

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['_method'] = 'DELETE' # to support REST delete method
        return self.fetch_resource("http://api.twitter.com/%d/%s/lists/%s.json"%(version, user, id), kwargs, 'POST')
    
    @_simple_decorator
    def user_list_statuses_get(self, user, id, version=None, **kwargs):
        """user_list_statuses_get(user, id)
        
        Show tweet timeline for members of the specified list.
        
        Parameters:
            user - username
            
            id - The id or slug of the list.
            
            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.

            max_id - Returns results with an ID less than (that is, older than)
                     or equal to the specified ID.

            per_page - Specifies the page of results to retrieve.

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
        return self.opener.open("http://api.twitter.com/%d/%s/lists/%s/statuses.json?%s"%(version, user, id, urllib.urlencode(kwargs)))
        
    @_authentication_required
    def user_list_memberships_get(self, user, version=None, **kwargs):
        """user_list_memberships_get(user)
        
        List the lists the specified user has been added to.
        
        Parameters:
            user - username
            
            cursor - Breaks the results into pages. A single page contains 20
                     lists. Provide a value of -1 to begin paging. Provide
                     values as returned in the response body's next_cursor and
                     previous_cursor attributes to page back and forth in the list. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/%s/lists/memberships.json"%(version, user), kwargs)
    
    @_authentication_required
    def user_list_subscriptions_get(self, user, version=None, **kwargs):
        """user_list_subscriptions_get(user)
        
        List the lists the specified user follows.
        
        Parameters:
            user - username
            
            cursor - Breaks the results into pages. A single page contains 20
                     lists. Provide a value of -1 to begin paging. Provide
                     values as returned in the response body's next_cursor and
                     previous_cursor attributes to page back and forth in the list. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/%s/lists/subscriptions.json"%(version, user), kwargs)
    
    ############################################################################
    ## List members methods
    ############################################################################
    
    @_authentication_required
    def user_list_members_get(self, user, id, version=None, **kwargs):
        """user_list_members_get(user, id)
        
        Returns the members of the specified list.
        
        Parameters:
            user - username
            
            id - The id or slug of the list. 
            
            cursor - Breaks the results into pages. A single page contains 20
                     lists. Provide a value of -1 to begin paging. Provide
                     values as returned in the response body's next_cursor and
                     previous_cursor attributes to page back and forth in the list. 
                     
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
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/members.json"%(version, user, id), kwargs)
    
    @_authentication_required
    def user_list_members_add(self, user, list_id, user_id, version=None, **kwargs):
        """user_list_members_add(user, list_id, user_id)
        
        Add a member to a list. The authenticated user must own the list to be
        able to add members to it. Lists are limited to having 500 members.
        
        Parameters:
            user - username
            
            list_id - The id or slug of the list. 
            
            user_id - The user id of the list member.

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['id'] = user_id
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/members.json"%(version, user, list_id), kwargs, 'POST')
    
    @_authentication_required
    def user_list_members_create_all(self, user, list_id, ids, screen_names, version=None, **kwargs):
        """user_list_members_create_all(user, list_id, ids, screen_names)
        
        Adds multiple members to a list, by specifying a comma-separated list of
        member ids or screen names. The authenticated user must own the list to
        be able to add members to it. Lists are limited to having 500 members,
        and you are limited to adding up to 100 members to a list at a time with
        this method.
        
        Parameters:
            user - username
            
            list_id - The id or slug of the list.
            
            ids - iterable object with users id.

            screen_names - iterable object with screen_names. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if ids is not None:
            kwargs['user_id'] = ','.join(ids)
        if screen_names is not None:
            kwargs['screen_name'] = ','.join(screen_names)
        return self.fetch_resource("http://api.twitter.com/%s/%s/%s/create_all.json"%(version, user, list_id), kwargs, 'POST')
    
    @_authentication_required
    def user_list_members_delete(self, user, list_id, user_id, version=None, **kwargs):
        """user_list_members_delete(user, list_id, user_id)
        
        Removes the specified member from the list. The authenticated user must
        be the list's owner to remove members from the list.
        
        Parameters:
            user - username
            
            list_id - The id or slug of the list. 
            
            user_id - The user id of the list member.

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['id'] = user_id
        kwargs['_method'] = 'DELETE'
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/members.json"%(version, user, list_id), kwargs, 'POST')
        
    @_authentication_required
    def user_list_is_member(self, user, list_id, user_id, version=None, **kwargs):
        """user_list_is_member(user, list_id, user_id)
        
        Check if a user is a member of the specified list.
        
        Parameters:
            user - username
            
            list_id - The id or slug of the list. 
            
            user_id - The user id of the list member.
            
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
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/members/%s.json"%(version, user, list_id, user_id), kwargs)
    
    ############################################################################
    ## List subscribers methods
    ############################################################################
    
    @_authentication_required
    def user_list_subscribers_get(self, user, id, version=None, **kwargs):
        """user_list_subscribers_get(user, id)
        
        Returns the subscribers of the specified list.
        
        Parameters:
            user - username
            
            id - The id or slug of the list. 
            
            cursor - Breaks the results into pages. A single page contains 20
                     lists. Provide a value of -1 to begin paging. Provide
                     values as returned in the response body's next_cursor and
                     previous_cursor attributes to page back and forth in the list. 
                     
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
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/subscribers.json"%(version, user, id), kwargs)
    
    @_authentication_required
    def user_list_subscribers(self, user, list_id, version=None, **kwargs):
        """user_list_subscribers(user, list_id)
        
        Make the authenticated user follow the specified list.
        
        Parameters:
            user - username
            
            list_id - The id or slug of the list. 
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/subscribers.json"%(version, user, list_id), kwargs, 'POST')
    
    @_authentication_required
    def user_list_subscribers_delete(self, user, list_id, version=None, **kwargs):
        """user_list_subscribers_delete(user, list_id)
        
        Unsubscribes the authenticated user form the specified list.
        
        Parameters:
            user - username of current user authenticated
            
            list_id - The id or slug of the list. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['_method'] = 'DELETE'
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/subscribers.json"%(version, user, list_id), kwargs, 'POST')
            
    @_authentication_required
    def user_list_is_subscriber(self, user, list_id, user_id, version=None, **kwargs):
        """user_list_is_subscriber(user, list_id, user_id)
        
        Check if a user is a subscriber of the specified list.
        
        Parameters:
            user - username of current user authenticated
            
            list_id - The id or slug of the list. 
            
            user_id - The user id of the list member.
            
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
        return self.fetch_resource("http://api.twitter.com/%d/%s/%s/subscribers/%s.json"%(version, user, list_id, user_id), kwargs)
    
    ############################################################################
    ## Direct messages methods
    ############################################################################
    
    @_authentication_required
    def direct_messages_get(self, version=None, **kwargs):
        """direct_messages_get()

        Returns the 20 most recent direct messages sent to the authenticating
        user. The XML and JSON versions include detailed information about the
        sender and recipient user.


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
        return self.fetch_resource("http://api.twitter.com/%d/direct_messages.json"%(version), kwargs)
            
    @_authentication_required
    def direct_messages_sent_get(self, version=None, **kwargs):
        """direct_messages_sent_get()

        Returns the 20 most recent direct messages sent by the authenticating
        user. The XML and JSON versions include detailed information about the
        sender and recipient user.

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
        return self.fetch_resource("http://api.twitter.com/%d/direct_messages/sent.json"%(version), kwargs)
    
    @_authentication_required
    def direct_messages_new(self, text, user_id=None, screen_name=None, version = None, **kwargs):
        """direct_messages_new(text, user_id, screen_name)

        Sends a new direct message to the specified user from the authenticating
        user. Requires both the user and text parameters and must be a POST.
        Returns the sent message in the requested format if successful.


        Parameters:
            screen_name - The screen name of the user who should receive the
                          direct message. Helpful for disambiguating when a
                          valid screen name is also a user ID.

            user_id - The ID of the user who should receive the direct message.
                      Helpful for disambiguating when a valid user ID is also a
                      valid screen name.

            text - The text of your direct message. Be sure to URL encode as
                   necessary, and keep the message under 140 characters.

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
        if user_id is None and screen_name is None:
            raise RequestError('direct_messages_new(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/direct_messages/new.json"%(version), kwargs, 'POST')        

    @_authentication_required
    def direct_messages_destroy(self, id, version=None, **kwargs):
        """direct_messages_destroy(id)

        Destroys the direct message specified in the required ID parameter. The
        authenticating user must be the recipient of the specified direct message.

       	Parameters:
            id - The ID of the direct message to delete. 

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
        return self.fetch_resource("http://api.twitter.com/%d/direct_messages/destroy/%s.json" % (version, id), kwargs, 'POST')
    
    ############################################################################
    ## Friendship methods
    ############################################################################
    
    @_authentication_required
    def friendship_create(self, version=None, **kwargs):
        """friendship_create()

        Allows the authenticating users to follow the user specified in the ID
        parameter.

        Returns the befriended user in the requested format when successful.
        Returns a string describing the failure condition when unsuccessful. If
        you are already friends with the user an HTTP 403 will be returned.

       	Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID.

            follow - Enable notifications for the target user.  
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/friendships/create.json"%(version), kwargs, 'POST')
    
    @_authentication_required    
    def friendship_destroy(self, version=None, **kwargs):
        """friendship_destroy()

        Allows the authenticating users to unfollow the user specified in the ID
        parameter.

        Returns the unfollowed user in the requested format when successful.
        Returns a string describing the failure condition when unsuccessful.

       	Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID.
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/friendships/destroy.json"%(version), kwargs, 'POST')
    
    @_simple_decorator
    def friendship_exists(self, user_a, user_b, version=None, **kwargs):
        """friendship_exists()
    
        Test for the existence of friendship between two users. Will return true
        if user_a follows user_b, otherwise will return false.

        Consider using friendships/show instead of this method.

       	Parameters:
            user_a - The ID or screen_name of the subject user.

            user_b - The ID or screen_name of the user to test for following. 
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['user_a'] = user_a
        kwargs['user_b'] = user_b
        return self.fetch_resource("http://api.twitter.com/%d/friendships/exists.json"%(version), kwargs)
        
    @_simple_decorator
    def friendship_show(self, version=None, **kwargs):
        """friendship_show()
    
        Returns detailed information about the relationship between two users.

       	Parameters:
            source_id - The user_id of the subject user.

            source_screen_name - The screen_name of the subject user.

            target_id - The user_id of the target user.

            target_screen_name - The screen_name of the target user.  
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/friendships/show.json"%(version), kwargs)
    
    @_authentication_required
    def friendship_incoming(self, version=None, **kwargs):
        """friendship_incoming()
    
        Returns detailed information about the relationship between two users.

       	Parameters:
            cursor - Breaks the results into pages. This is recommended for
                     users who are following many users. Provide a value of -1
                     to begin paging. Provide values as returned in the response
                     body's next_cursor and previous_cursor attributes to page
                     back and forth in the list.   
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/friendships/incoming.json"%(version), kwargs)
    
    @_authentication_required
    def friendship_outgoing(self, version=None, **kwargs):
        """friendship_outgoing()
    
        Returns an array of numeric IDs for every protected user for whom the
        authenticating user has a pending follow request.

       	Parameters:
            cursor - Breaks the results into pages. This is recommended for
                     users who are following many users. Provide a value of -1
                     to begin paging. Provide values as returned in the response
                     body's next_cursor and previous_cursor attributes to page
                     back and forth in the list.   
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/friendships/outgoing.json"%(version), kwargs)
        
    ############################################################################
    ## Friends and Followers methods
    ############################################################################
    
    @_simple_decorator
    def friendship_ids_get(self, user_id=None, screen_name=None, version=None, **kwargs):
        """friendship_ids_get(user_id, screen_name=None)
            
        Returns an array of numeric IDs for every user the specified user is
        following.

       	Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            cursor - Causes the list of connections to be broken into pages of
                     no more than 5000 IDs at a time. The number of IDs returned
                     is not guaranteed to be 5000 as suspended users are filterd
                     out after connections are queried.
                     To begin paging provide a value of -1 as the cursor. The
                     response from the API will include a previous_cursor and
                     next_cursor to allow paging back and forth.
                     If the cursor is not provided the API will attempt to
                     return all IDs. For users with many connections this will
                     probably fail. Querying without the cursor parameter is
                     deprecated and should be avoided. The API is being updated
                     to force the cursor to be -1 if it isn't supplied.    
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('friendship_ids_get(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/friends/ids.json"%(version), kwargs)
    
    @_simple_decorator
    def followers_ids_get(self, user_id=None, screen_name=None, version=None, **kwargs):
        """followers_ids_get(user_id, screen_name=None)
            
        Returns an array of numeric IDs for every user following the specified user.

       	Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            cursor - Causes the list of connections to be broken into pages of
                     no more than 5000 IDs at a time. The number of IDs returned
                     is not guaranteed to be 5000 as suspended users are filterd
                     out after connections are queried.
                     To begin paging provide a value of -1 as the cursor. The
                     response from the API will include a previous_cursor and
                     next_cursor to allow paging back and forth.
                     If the cursor is not provided the API will attempt to
                     return all IDs. For users with many connections this will
                     probably fail. Querying without the cursor parameter is
                     deprecated and should be avoided. The API is being updated
                     to force the cursor to be -1 if it isn't supplied.    
                               
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('followers_ids_get(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/followers/ids.json"%(version), kwargs)

    ############################################################################
    ## Friends and Followers methods
    ############################################################################
    
    @_authentication_required
    def verify_credentials(self, version=None, **kwargs):
        """ verify_credentials(self, version=None):

        Returns an HTTP 200 OK response code and a representation of the
        requesting user if authentication was successful; returns a 401 status
        code and an error message if not. Use this method to test if supplied
        user credentials are valid.

        Parameters:
             include_entities - When set to either true, t or 1, each tweet
                                will include a node called "entities,". This
                                node offers a variety of metadata about the
                                tweet in a discreet structure, including:
                                user_mentions, urls, and hashtags. While
                                entities are opt-in on timelines at present,
                                they will be made a default component of output
                                in the future. See Tweet Entities for more detail
                                on entities. 
                                
             version (number) - API version to request. Entire mtweets class
                                defaults to 1, but you can override on a 
                                function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/account/verify_credentials.json"%version, kwargs)
    
    @_simple_decorator
    def rate_limit_status(self, version=None, **kwargs):
        """ verify_credentials(self, version=None):

        Returns the remaining number of API requests available to the requesting
        user before the API limit is reached for the current hour. Calls to
        rate_limit_status do not count against the rate limit. If authentication
        credentials are provided, the rate limit status for the authenticating
        user is returned. Otherwise, the rate limit status for the requester's
        IP address is returned. Learn more about the REST API rate limiting.

        Parameters:                                
             version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/account/rate_limit_status.json"%version, kwargs)
    
    @_authentication_required
    def end_session(self, version = None):
        """endSession()

        Ends the session of the authenticating user, returning a null cookie. 
        Use this method to sign users out of client-facing applications (widgets, etc).

        Parameters:
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/account/end_session.json" % version)
    
    @_authentication_required
    def delivery_device_update(self, device_name="none", version=None, **kwargs):
        """delivery_device_update(device_name="none")

       	Sets which device Twitter delivers updates to for the authenticating
        user. Sending none as the device parameter will disable SMS updates.

        Parameters:
            device_name - Must be one of: sms, im, none.
            
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['device'] = device_name
        return self.fetch_resource("http://api.twitter.com/%d/account/update_delivery_device.json"%version, kwargs, 'POST')
    
    @_authentication_required
    def profile_colors_update(self, version=None, **kwargs):
        """profile_colors_update()

        Sets one or more hex values that control the color scheme of the
        authenticating user's profile page on twitter.com. Each parameter's
        value must be a valid hexidecimal value, and may be either three or six
        characters (ex: #fff or #ffffff).

        Parameters:
            profile_background_color - Profile background color.
            
            profile_text_color - Profile text color.
            
            profile_link_color - Profile link color.
            
            profile_sidebar_fill_color - Profile sidebar's background color.
            
            profile_sidebar_border_color - Profile sidebar's border color. 

            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/account/update_profile_colors.json"%version, kwargs, 'POST')
    
    @_authentication_required
    def profile_image_image(self, filename, version=None, **kwargs):
        """ profile_image_image(filename)

        Updates the authenticating user's profile image. Note that this method
        expects raw multipart data, not a URL to an image.
        This method asynchronously processes the uploaded file before updating
        the user's profile image URL. You can either update your local cache the
        next time you request the user's information, or, at least 5 seconds
        after uploading the image, ask for the updated URL using
        users/profile_image/:screen_name.


        Parameters:
            image - The avatar image for the profile. Must be a valid GIF, JPG,
                    or PNG image of less than 700 kilobytes in size. Images with
                    width larger than 500 pixels will be scaled down. Animated
                    GIFs will be converted to a static GIF of the first frame,
                    removing the animation.
                    
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        
        ## FIXME: improve this method
        version = version or self.apiVersion
        files = [("image", filename, open(filename, 'rb').read())]
        fields = []
        content_type, body = self._encode_multipart_formdata(fields, files)
        old_headers = self.opener.addheaders
        self.opener.addheaders = [('Content-Type', content_type), ('Content-Length', str(len(body)))].extends(self.opener.addheaders)
        kwargs[''] = body
        data = self.fetch_resource("http://api.twitter.com/%d/account/update_profile_image.json"%version, kwargs, 'POST')
        self.opener.addheaders = old_headers
        return data
        
    @_authentication_required
    def profile_background_image_update(self, filename, version=None, **kwargs):
        """ profile_background_image_update(filename, tile="true")

        Updates the authenticating user's profile background image.

        Parameters:
            image - The avatar image for the profile. Must be a valid GIF, JPG,
                    or PNG image of less than 700 kilobytes in size. Images with
                    width larger than 500 pixels will be scaled down. Animated
                    GIFs will be converted to a static GIF of the first frame,
                    removing the animation.
                    
            tile - Whether or not to tile the background image. If set to true
                   the background image will be displayed tiled. The image will
                   not be tiled otherwise.  
                    
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        ## FIXME: improve this method
        version = version or self.apiVersion
        files = [("image", filename, open(filename, 'rb').read())]
        fields = []
        content_type, body = self._encode_multipart_formdata(fields, files)
        old_headers = self.opener.addheaders
        self.opener.addheaders = [('Content-Type', content_type), ('Content-Length', str(len(body)))].extends(self.opener.addheaders)
        kwargs[''] = body
        data = self.fetch_resource("http://api.twitter.com/%d/account/update_profile_background_image.json"%version, kwargs, 'POST')
        self.opener.addheaders = old_headers
        return data

    @_authentication_required
    def profile_update(self, version=None, **kwargs):
        """profile_update()

        Sets values that users are able to set under the "Account" tab of their
        settings page.  Only the parameters specified will be updated.

        Parameters:
            name - Full name associated with the profile. Maximum of 20 characters.
            
            url - URL associated with the profile. Will be prepended with
                  "http://" if not present. Maximum of 100 characters.

            location - The city or country describing where the user of the
                       account is located. The contents are not normalized or
                       geocoded in any way. Maximum of 30 characters.

            description - A description of the user owning the account. Maximum
                          of 160 characters.
                          
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.

        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/account/update_profile.json"%version, kwargs, 'POST')

    ############################################################################
    ## Favorities methods
    ############################################################################
    
    @_authentication_required
    def favorites_get(self, id=None, version=None, **kwargs):
        """favorites_get(id=None)

        Returns the 20 most recent favorite statuses for the authenticating user
        or user specified by the ID parameter in the requested format.

        Parameters:
            id - The ID or screen name of the user for whom to request a list of
                 favorite statuses. Note this isn't a query string parameter but
                 a change to the end of the URL.

            page - Specifies the page of results to retrieve.

            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        if id is not None:
            url = "http://api.twitter.com/%d/favorites/%s.json"%(version, id)
        else:
            url = "http://api.twitter.com/%d/favorites.json"%(version)
        return self.fetch_resource(url, kwargs)
    
    @_authentication_required
    def favorite_create(self, id, version=None, **kwargs):
        """favorite_create(id)

        Favorites the status specified in the ID parameter as the authenticating
        user. Returns the favorite status when successful.

        Parameters:
            id - The numerical ID of the desired status. 
             
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/favorites/create/%s.json"%(version, id), kwargs, 'POST')
    
    @_authentication_required
    def favorite_destroy(self, id, version=None, **kwargs):
        """favorite_destroy(id)

        Un-favorites the status specified in the ID parameter as the
        authenticating user. Returns the un-favorited status in the requested
        format when successful.

        Parameters:
            id - The numerical ID of the desired status. 
             
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/favorites/destroy/%s.json"%(version, id), kwargs, 'POST')
        
    ############################################################################
    ## Notification methods
    ############################################################################
    
    @_authentication_required
    def notification_follow(self, user_id=None, screen_name=None, version=None, **kwargs):
        """notification_follow()

        Enables device notifications for updates from the specified user.
        Returns the specified user when successful.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('notification_follow(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/notifications/follow.json"%(version), kwargs, 'POST')
    
    @_authentication_required
    def notification_leave(self, user_id=None, screen_name=None, version=None, **kwargs):
        """notification_leave()

        Disables notifications for updates from the specified user to the
        authenticating user. Returns the specified user when successful.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('notification_leave(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/notifications/leave.json"%(version), kwargs, 'POST')
    
    ############################################################################
    ## Block methods
    ############################################################################
    
    @_authentication_required
    def block_create(self, user_id=None, screen_name=None, version=None, **kwargs):
        """block_create()

        Blocks the user specified in the ID parameter as the authenticating
        user. Destroys a friendship to the blocked user if it exists. Returns
        the blocked user in the requested format when successful.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('block_create(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/blocks/create.json"%(version), kwargs, 'POST')

    @_authentication_required
    def block_destroy(self, user_id=None, screen_name=None, version = None):
        """block_destroy()

        Un-blocks the user specified in the ID parameter for the authenticating
        user. Returns the un-blocked user in the requested format when successful.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('block_destroy(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/blocks/destroy.json"%(version), kwargs, 'POST')

    @_authentication_required
    def block_exists(self, user_id=None, screen_name=None, version=None, **kwargs):
        """block_exists()

        Returns if the authenticating user is blocking a target user. Will
        return the blocked user's object if a block exists, and error with a
        HTTP 404 response code otherwise.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('block_exists(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/blocks/exists.json"%(version), kwargs)
    
    @_authentication_required
    def block_get(self, version=None, **kwargs):
        """block_get()

        Returns an array of user objects that the authenticating user is blocking.

        Parameters:
            page - Specifies the page of results to retrieve.
            
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/blocks/blocking.json"%(version), kwargs)
    
    @_authentication_required
    def blocked_get_ids(self, version=None):
        """blocked_get_ids()

        Returns an array of numeric user ids the authenticating user is blocking.

        Parameters:
            version (number) - Optional. API version to request. Entire mtweets class defaults to 1, but you can override on a function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/blocks/blocking/ids.json"%(version))
    
    ############################################################################
    ## Spam methods
    ############################################################################
    
    @_authentication_required
    def report_spam(self, user_id=None, screen_name=None, version=None, **kwargs):
        """reportSpam():

        The user specified in the id is blocked by the authenticated user and
        reported as a spammer.

        Parameters:
            user_id - The ID of the user for whom to return results for. Helpful
                      for disambiguating when a valid user ID is also a valid
                      screen name.

            screen_name - The screen name of the user for whom to return results
                          for. Helpful for disambiguating when a valid screen
                          name is also a user ID. 
                          
            include_entities - When set to either true, t or 1, each tweet
                               will include a node called "entities,". This
                               node offers a variety of metadata about the
                               tweet in a discreet structure, including:
                               user_mentions, urls, and hashtags. While
                               entities are opt-in on timelines at present,
                               they will be made a default component of output
                               in the future. See Tweet Entities for more detail
                               on entities. 

            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        if user_id is None and screen_name is None:
            raise RequestError('report_spam(): Need one of the following parameter: user_id or screen_name')
        
        version = version or self.apiVersion
        
        if user_id is not None:
            kwargs['user_id'] = user_id
        if screen_name is not None:
            kwargs['screen_name'] = screen_name
            
        return self.fetch_resource("http://api.twitter.com/%d/report_spam.json"%(version), kwargs)
    
    ############################################################################
    ## saved searches methods
    ############################################################################
    
    @_authentication_required
    def saved_searches_get(self, version=None):
        """saved_searches_get()

        Returns the authenticated user's saved search queries.

       	Parameters:
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/saved_searches.json"%(version))
    
    @_authentication_required
    def saved_searches_show(self, id, version=None):
        """saved_searches_show(id)

        Retrieve the data for a saved search owned by the authenticating user
        specified by the given id.

        Parameters:
            id - The id of the saved search to be retrieved.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/saved_searches/show/%s.json"%(version, id))
    
    def saved_searches_create(self, query, version=None):
        """saved_searches_create(query)

        Creates a saved search for the authenticated user.

        Parameters:
            query - The query of the search the user would like to save.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs = {'query':query}
        return self.fetch_resource("http://api.twitter.com/%d/saved_searches/create.json"%(version), kwargs, 'POST')
    
    @_authentication_required
    def saved_searches_destroy(self, id, version = None):
        """ saved_searches_destroy(id)

        Destroys a saved search for the authenticated user. The search specified
        by id must be owned by the authenticating user.

        Parameters:
            id - The id of the saved search to be deleted.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/saved_searches/destroy/%s.json"%(version, id), http_method='POST')
    
    ############################################################################
    ## Geo methods
    ############################################################################
    
    @_simple_decorator
    def geo_search(self, version=None, **kwargs):
        """ geo_search()

        Search for places that can be attached to a statuses/update. Given a
        latitude and a longitude pair, an IP address, or a name, this request
        will return a list of all the valid places that can be used as the
        place_id when updating a status.

        Conceptually, a query can be made from the user's location, retrieve a
        list of places, have the user validate the location he or she is at, and
        then send the ID of this location with a call to statuses/update.

        This is the recommended method to use find places that can be attached
        to statuses/update. Unlike geo/reverse_geocode which provides raw data
        access, this endpoint can potentially re-order places with regards to
        the user who is authenticated. This approach is also preferred for
        interactive place matching with the user.

        Parameters:
            lat - The latitude to search around. This parameter will be ignored
                  unless it is inside the range -90.0 to +90.0 (North is 
                  positive) inclusive. It will also be ignored if there isn't a
                  corresponding long parameter.
                  
            long - The longitude to search around. The valid ranges for
                   longitude is -180.0 to +180.0 (East is positive) inclusive.
                   This parameter will be ignored if outside that range, if it
                   is not a number, if geo_enabled is disabled, or if there not
                   a corresponding lat parameter.
            
            query - Free-form text to match against while executing a geo-based
                    query, best suited for finding nearby locations by name.
                    Remember to URL encode the query.
                    
            ip - An IP address. Used when attempting to fix geolocation based
                 off of the user's IP address.
                 
            granularity - This is the minimal granularity of place types to
                          return and must be one of: poi, neighborhood, city,
                          admin or country. If no granularity is provided for
                          the request neighborhood is assumed.
                          Setting this to city, for example, will find places
                          which have a type of city, admin or country.
          
            accuracy - A hint on the "region" in which to search. If a number,
                       then this is a radius in meters, but it can also take a
                       string that is suffixed with ft to specify feet. If this
                       is not passed in, then it is assumed to be 0m. If coming
                       from a device, in practice, this value is whatever
                       accuracy the device has measuring its location (whether
                       it be coming from a GPS, WiFi triangulation, etc.).
          
            max_results - A hint as to the number of results to return. This
                          does not guarantee that the number of results returned
                          will equal max_results, but instead informs how many
                          "nearby" results to return. Ideally, only pass in the
                          number of places you intend to display to the user here.
          
            contained_within - This is the place_id which you would like to
                               restrict the search results to. Setting this
                               value means only places within the given place_id
                               will be found.
                               Specify a place_id. For example, to scope all 
                               results to places within "San Francisco, CA USA",
                               you would specify a place_id of "5a110d312052166f"
          
            attribute:street_address - This parameter searches for places which
                                       have this given street address. There are
                                       other well-known, and application
                                       specific attributes available. Custom
                                       attributes are also permitted. Learn more
                                       about Place Attributes.

           callback - If supplied, the response will use the JSONP format with a
                      callback of the given name.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/geo/search.json"%(version), kwargs)
    
    @_simple_decorator
    def geo_similar_places(self, lat, long, name, version=None, **kwargs):
        """ geo_similar_places(lat, long, name)

        Locates places near the given coordinates which are similar in name.

        Conceptually you would use this method to get a list of known places to
        choose from first. Then, if the desired place doesn't exist, make a
        request to post/geo/place to create a new one.

        The token contained in the response is the token needed to be able to
        create a new place.

        Parameters:
            lat - The latitude to search around. This parameter will be ignored
                  unless it is inside the range -90.0 to +90.0 (North is 
                  positive) inclusive. It will also be ignored if there isn't a
                  corresponding long parameter.
                  
            long - The longitude to search around. The valid ranges for
                   longitude is -180.0 to +180.0 (East is positive) inclusive.
                   This parameter will be ignored if outside that range, if it
                   is not a number, if geo_enabled is disabled, or if there not
                   a corresponding lat parameter.
                   
            name - The name a place is known as. 
            
            contained_within - This is the place_id which you would like to
                               restrict the search results to. Setting this
                               value means only places within the given place_id
                               will be found.
                               Specify a place_id. For example, to scope all 
                               results to places within "San Francisco, CA USA",
                               you would specify a place_id of "5a110d312052166f"
          
            attribute:street_address - This parameter searches for places which
                                       have this given street address. There are
                                       other well-known, and application
                                       specific attributes available. Custom
                                       attributes are also permitted. Learn more
                                       about Place Attributes.

           callback - If supplied, the response will use the JSONP format with a
                      callback of the given name.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['lat'] = lat
        kwargs['long'] = long
        kwargs['name'] = name
        return self.fetch_resource("http://api.twitter.com/%d/geo/similar_places.json"%(version), kwargs)
    
    @_simple_decorator
    def geo_reverse_geocode(self, lat, long, version=None, **kwargs):
        """ geo_reverse_geocode(lat, long)

        Given a latitude and a longitude, searches for up to 20 places that can
        be used as a place_id when updating a status.

        This request is an informative call and will deliver generalized results
        about geography.

        Parameters:
            lat - The latitude to search around. This parameter will be ignored
                  unless it is inside the range -90.0 to +90.0 (North is 
                  positive) inclusive. It will also be ignored if there isn't a
                  corresponding long parameter.
                  
            long - The longitude to search around. The valid ranges for
                   longitude is -180.0 to +180.0 (East is positive) inclusive.
                   This parameter will be ignored if outside that range, if it
                   is not a number, if geo_enabled is disabled, or if there not
                   a corresponding lat parameter.
            
            granularity - This is the minimal granularity of place types to
                          return and must be one of: poi, neighborhood, city,
                          admin or country. If no granularity is provided for
                          the request neighborhood is assumed.
                          Setting this to city, for example, will find places
                          which have a type of city, admin or country.
          
            accuracy - A hint on the "region" in which to search. If a number,
                       then this is a radius in meters, but it can also take a
                       string that is suffixed with ft to specify feet. If this
                       is not passed in, then it is assumed to be 0m. If coming
                       from a device, in practice, this value is whatever
                       accuracy the device has measuring its location (whether
                       it be coming from a GPS, WiFi triangulation, etc.).
          
            max_results - A hint as to the number of results to return. This
                          does not guarantee that the number of results returned
                          will equal max_results, but instead informs how many
                          "nearby" results to return. Ideally, only pass in the
                          number of places you intend to display to the user here.
          
           callback - If supplied, the response will use the JSONP format with a
                      callback of the given name.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/geo/reverse_geocode.json"%(version), kwargs)
    
    @_simple_decorator
    def geo_id(self, place_id, version=None):
        """ geo_id(place_id)

        Returns all the information about a known place.

        Parameters:
            place_id - A place in the world. These IDs can be retrieved from
                       geo/reverse_geocode. 
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.fetch_resource("http://api.twitter.com/%d/geo/id/%s.json"%(version, place_id))
    
    @_authentication_required
    def geo_place(self, name, contained_within, token, lat, long, version=None, **kwargs):
        """ geo_place(place_id)

        Creates a new place at the given latitude and longitude.

        Parameters:
            name - The name a place is known as.

            contained_within - The place_id within which the new place can be
                               found. Try and be as close as possible with the
                               containing place. For example, for a room in a
                               building, set the contained_within as the
                               building place_id.

            token - The token found in the response from geo/similar_places.

            lat - The latitude the place is located at. This parameter will be
                  ignored unless it is inside the range -90.0 to +90.0 (North
                  is positive) inclusive. It will also be ignored if there isn't
                  a corresponding long parameter.

            long - The longitude the place is located at. The valid ranges for
                   longitude is -180.0 to +180.0 (East is positive) inclusive.
                   This parameter will be ignored if outside that range, if it
                   is not a number, if geo_enabled is disabled, or if there not
                   a corresponding lat parameter. 
                   
            attribute:street_address - This parameter searches for places which
                                       have this given street address. There are
                                       other well-known, and application
                                       specific attributes available. Custom
                                       attributes are also permitted. Learn more
                                       about Place Attributes.
          
            callback - If supplied, the response will use the JSONP format with
                       a callback of the given name.
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        kwargs['name'] = name
        kwargs['contained_within'] = contained_within
        kwargs['token'] = token
        kwargs['lat'] = lat
        kwargs['long'] = long
        return self.fetch_resource("http://api.twitter.com/%d/geo/place.json"%(version), kwargs, 'POST')
    
    ############################################################################
    ## Legal methods
    ############################################################################
    
    @_simple_decorator
    def legal_tos(self, version=None):
        """ legal_tos()

        Returns Twitter's' Terms of Service in the requested format. These are
        not the same as the Developer Terms of Service.

        Parameters:
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.opener.open("http://api.twitter.com/%d/legal/tos.json"%(version))
    
    @_simple_decorator
    def legal_privacy(self, version=None):
        """ legal_privacy()

        Returns Twitter's Privacy Policy in the requested format.

        Parameters:
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.opener.open("http://api.twitter.com/%d/legal/tos.json"%(version))
    
    ############################################################################
    ## Help methods
    ############################################################################
    
    @_simple_decorator
    def help_test(self, version=None):
        """ help_test()

        Returns the string "ok" in the requested format with a 200 OK HTTP status code.

        Parameters:
            
            version (number) - API version to request. Entire mtweets class
                               defaults to 1, but you can override on a 
                               function-by-function or class basis - (version=2), etc.
        """
        version = version or self.apiVersion
        return self.opener.open("http://api.twitter.com/%d/help/test..json"%(version))
    
    ############################################################################
    ## search methods
    ############################################################################

    @_simple_decorator
    def help_test(self, q, **kwargs):
        """ help_test()

        Returns the string "ok" in the requested format with a 200 OK HTTP status code.

        Parameters:            
            q - Search query. Should be URL encoded. Queries will be limited by
                complexity. 
                
            callback - Only available for JSON format. If supplied, the response
                       will use the JSONP format with a callback of the given name.
                       
            lang - Restricts tweets to the given language, given by an ISO 639-1
                   code.
                   
            locale - Specify the language of the query you are sending (only ja
                     is currently effective). This is intended for
                     language-specific clients and the default should work in
                     the majority of cases.

            rpp - The number of tweets to return per page, up to a max of 100.

            page - The page number (starting at 1) to return, up to a max of
                   roughly 1500 results (based on rpp * page).

            since_id - Returns results with an ID greater than (that is, more
                       recent than) the specified ID. There are limits to the
                       number of Tweets which can be accessed through the API.
                       If the limit of Tweets has occured since the since_id,
                       the since_id will be forced to the oldest ID available.

            until - Optional. Returns tweets generated before the given date.
                    Date should be formatted as YYYY-MM-DD.

            geocode - Returns tweets by users located within a given radius of
                      the given latitude/longitude. The location is preferentially
                      taking from the Geotagging API, but will fall back to their
                      Twitter profile. The parameter value is specified by
                      "latitude,longitude,radius", where radius units must be
                      specified as either "mi" (miles) or "km" (kilometers).
                      Note that you cannot use the near operator via the API to
                      geocode arbitrary locations; however you can use this
                      geocode parameter to search near geocodes directly.

            show_user - When true, prepends ":" to the beginning of the tweet.
                        This is useful for readers that do not display Atom's
                        author field. The default is false.
                        
            result_type - Optional. Specifies what type of search results you
                          would prefer to receive. The current default is "mixed."
                          Valid values include:

                               mixed: Include both popular and real time results in the response.
                               recent: return only the most recent results in the response
                               popular: return only the most popular results in the response.
        """
        version = version or self.apiVersion
        kwargs['q'] = q
        return self.opener.open("http://search.twitter.com/search.json?%s"%(urllib.urlencode(kwargs)))

    # The following methods are apart from the other Account methods, because they rely on a whole multipart-data posting function set.
    
    ############################################################################
    ## Other methods
    ############################################################################
    
    def _encode_multipart_formdata(self, fields, files):
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
            L.append('Content-Type: %s' % self._get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def _get_content_type(self, filename):
        """ get_content_type(self, filename)

        	Exactly what you think it does. :D
        """
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def _unicode2utf8(self, text):
        try:
            if isinstance(text, unicode):
                text = text.encode('utf-8')
        except:
            pass
        return text
    
