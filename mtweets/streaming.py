#!/usr/bin/python

"""mtweets - Easy Twitter utilities in Python

mtweets is an up-to-date library for Python that wraps the Twitter API.
Other Python Twitter libraries seem to have fallen a bit behind, and
Twitter's API has evolved a bit. Here's hoping this helps.

Please review the online twitter docs for concepts used by twitter:

    http://developer.twitter.com/doc

and stream api doc:

    http://developer.twitter.com/pages/streaming_api
"""
__author__ = "Luis C. Cruz <carlitos.kyo@gmail.com>"
__version__ = "0.1"

import httplib, urllib, urllib2, mimetypes, mimetools

from threading import Thread

from urlparse import urlparse
from urllib2 import HTTPError

from mtweets.utils import AuthError
from mtweets.utils import RequestError
from mtweets.utils import TwitterClient

class _Producer(Thread):
    """Simple thread that notify and sends new tweets to a reiciver.
    """
    
    def set_stream_callback(self, stream, callback):
        self.__stream = stream
        self.__callback = callback
        
    def run(self):
        for line in self.__stream:
            self.__callback(line)
    
    def close_stream(self):
        if not self.__stream.closed:
            self.__stream.close()

class Stream(TwitterClient):
    """ This handle simple authentication flow.
    
    For desktop application should set the verifier field into the token 
    returned by fetch_for_authorize method before call fetch_access_token method.    
    
    >>> import mtweet
    
    Desktop applications:
    
    * request for access tokens datastore_object should be the instance that 
      manage user token set the right user token to avoid security problems.
    
    >>> api = mtweet.Stream((key, secret), 'my app', True)
    >>> api.oauth_datastore = datastore_object
    >>> url, token = api.fetch_for_authorize()
    >>> token.set_verifier(pin)
    >>> api.fetch_access_token(token)
    
    Web applications:
    
    * request for access tokens datastore_object should be the instance that 
      manage user token set the right user token to avoid security problems
    
    >>> api = mtweet.Stream((key, secret), 'my app')
    >>> api.oauth_datastore = datastore_object
    >>> url, token = api.fetch_for_authorize() # redirect url
    >>> api.fetch_access_token(token) # call in a url, restore the token and then fetch for access
    
    Fetch for resources
    
    >>> api = mtweet.Stream((key, secret), 'my app', True)
    >>> api.oauth_datastore = datastore_object
    >>> api.firehorse(callback)
    
    where callback will reicive new tweets from the stream. 
    """
    
    ############################################################################
    ## Feeds implementation
    ############################################################################
    
    def filter(self, callback, **kwargs):
        """filter()

        Returns public statuses that match one or more filter predicates. At
        least one predicate parameter, track or follow, must be specified.
        Both parameters may be specified which allows most clients to use a
        single connection to the Streaming API. Placing long parameters in the
        URL may cause the request to be rejected for excessive URL length.
        Use a POST request header parameter to avoid long URLs.

        The default access level allows up to 200 track keywords and 400 follow
        userids. Increased access levels allow 80,000 follow userids ("shadow"
        role), 400,000 follow userids ("birddog" role), 10,000 track keywords
        ("restricted track" role), and 200,000 track keywords ("partner track"
        role). Increased track access levels also pass a higher proportion of
        statuses before limiting the stream.
        
        Parameters:
            count - Indicates the number of previous statuses to consider for
                    delivery before transitioning to live stream delivery. On
                    unfiltered streams, all considered statuses are delivered,
                    so the number requested is the number returned. On filtered
                    streams, the number requested is the number of statuses that
                    are applied to the filter predicate, and not the number of
                    statuses returned. Firehose, Retweet, Link, Birddog and
                    Shadow clients interested in capturing all statuses should
                    maintain a current estimate of the number of statuses
                    received per second and note the time that the last status
                    was received. Upon a reconnect, the client can then estimate
                    the appropriate backlog to request. The count parameter is
                    not allowed on other resources and the default filter role.
                    
            delimited - Indicates that statuses should be delimited in the
                        stream. Statuses are represented by a length, in bytes,
                        a newline, and the status text that is exactly length
                        bytes. Note that "keep-alive" newlines may be inserted
                        before each length.
                        
            follow - Returns public statuses that reference the given set of
                     users. Users specified by a comma separated list.
                     References matched are statuses that were: Created by a
                     specified user Explicitly in-reply-to a status created by a
                     specified user (pressed reply "swoosh" button) Explicitly
                     retweeted by a specified user (pressed retweet button)
                     Created by a specified user and subsequently explicitly
                     retweed by any user References unmatched are statuses that
                     were: Mentions ("Hello @user!") Implicit replies ("@user
                     Hello!", created without pressing a reply "swoosh" button
                     to set the in_reply_to field) Implicit retweets ("RT @user
                     Says Helloes" without pressing a retweet button)
                     
            track - Specifies keywords to track. Keywords are specified by a
                    comma separated list. Queries are subject to Track
                    Limitations, described in Track Limiting and subject to
                    access roles, describe in the statuses/filter method. Track
                    keywords are case-insensitive logical ORs. Terms are
                    exact-matched, and also exact-matched ignoring punctuation.
                    Phrases, keywords with spaces, are not supported. Keywords
                    containing punctuation will only exact match tokens. Some
                    UTF-8 keywords will not match correctly- this is a known
                    temporary defect. Track examples: The keyword Twitter will
                    match all public statuses with the following comma delimited
                    tokens in their text field: TWITTER, twitter, "Twitter",
                    twitter., #twitter and @twitter. The following tokens will
                    not be matched: TwitterTracker and http://www.twitter.com,
                    The phrase, excluding quotes, "hard alee" won't match anything.
                    The keyword "helm's-alee" will match helm's-alee but not #helm's-alee.
        """
        if self.is_authorized():
            try:
                p = _Producer()
                p.set_stream_callback(self.fetch_resource("http://stream.twitter.com/statuses/filter.json", kwargs, 'POST'), callback)
                p.start()
                return p
            except HTTPError, e:
                raise RequestError("filter(): %s"%(e.msg), e.code)
        else:
            raise AuthError("filter(): requires you to be authenticated")
        
    def firehose(self, callback, **kwargs):
        """firehose()

        Returns all public statuses. The Firehose is not a generally available
        resource. Few applications require this level of access. Creative use of
        a combination of other resources and various access levels can satisfy
        nearly every application use case.
        
        Parameters:
            count - Indicates the number of previous statuses to consider for
                    delivery before transitioning to live stream delivery. On
                    unfiltered streams, all considered statuses are delivered,
                    so the number requested is the number returned. On filtered
                    streams, the number requested is the number of statuses that
                    are applied to the filter predicate, and not the number of
                    statuses returned. Firehose, Retweet, Link, Birddog and
                    Shadow clients interested in capturing all statuses should
                    maintain a current estimate of the number of statuses
                    received per second and note the time that the last status
                    was received. Upon a reconnect, the client can then estimate
                    the appropriate backlog to request. The count parameter is
                    not allowed on other resources and the default filter role.
                    
            delimited - Indicates that statuses should be delimited in the
                        stream. Statuses are represented by a length, in bytes,
                        a newline, and the status text that is exactly length
                        bytes. Note that "keep-alive" newlines may be inserted
                        before each length.
        """
        if self.is_authorized():
            try:
                p = _Producer()
                p.set_stream_callback(self.fetch_resource("http://stream.twitter.com/statuses/firehose.json", kwargs), callback)
                p.start()
                return p
            except HTTPError, e:
                raise RequestError("firehose(): %s"%(e.msg), e.code)
        else:
            raise AuthError("firehose(): requires you to be authenticated")
        
    def retweet(self, callback, **kwargs):
        """retweet()

        Returns all retweets. The retweet stream is not a generally available
        resource. Few applications require this level of access. Creative use of
        a combination of other resources and various access levels can satisfy
        nearly every application use case.
        
        Parameters:
            delimited - Indicates that statuses should be delimited in the
                        stream. Statuses are represented by a length, in bytes,
                        a newline, and the status text that is exactly length
                        bytes. Note that "keep-alive" newlines may be inserted
                        before each length.
        """
        if self.is_authorized():
            try:
                p = _Producer()
                p.set_stream_callback(self.fetch_resource("http://stream.twitter.com/statuses/retweet.json", kwargs), callback)
                p.start()
                return p
            except HTTPError, e:
                raise RequestError("retweet(): %s"%(e.msg), e.code)
        else:
            raise AuthError("retweet(): requires you to be authenticated")
        
    def sample(self, callback, **kwargs):
        """sample()

        Returns a random sample of all public statuses. The default access level
        provides a small proportion of the Firehose. The "Gardenhose" access
        level provides a proportion more suitable for data mining and research
        applications that desire a larger proportion to be statistically
        significant sample.
        
        Parameters:
            count - Indicates the number of previous statuses to consider for
                    delivery before transitioning to live stream delivery. On
                    unfiltered streams, all considered statuses are delivered,
                    so the number requested is the number returned. On filtered
                    streams, the number requested is the number of statuses that
                    are applied to the filter predicate, and not the number of
                    statuses returned. Firehose, Retweet, Link, Birddog and
                    Shadow clients interested in capturing all statuses should
                    maintain a current estimate of the number of statuses
                    received per second and note the time that the last status
                    was received. Upon a reconnect, the client can then estimate
                    the appropriate backlog to request. The count parameter is
                    not allowed on other resources and the default filter role.
                    
            delimited - Indicates that statuses should be delimited in the
                        stream. Statuses are represented by a length, in bytes,
                        a newline, and the status text that is exactly length
                        bytes. Note that "keep-alive" newlines may be inserted
                        before each length.
        """
        if self.is_authorized():
            try:
                p = _Producer()
                p.set_stream_callback(self.fetch_resource("http://stream.twitter.com/statuses/sample.json", kwargs), callback)
                p.start()
                return p
            except HTTPError, e:
                raise RequestError("sample(): %s"%(e.msg), e.code)
        else:
            raise AuthError("sample(): requires you to be authenticated")

