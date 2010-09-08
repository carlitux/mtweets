import sys, os
import pickle

sys.path.append('%s/oauth/'%(os.getcwd()))

from mtweets import API
from mtweets import Stream
from oauth import OAuthDataStoreMixin

class DataStore(OAuthDataStoreMixin):
    
    def save_token(self, oauth_token):
        file = open('token.data', 'w')
        pickle.dump(oauth_token, file)
        file.close()
    
    def delete_token(self):
        """-> OAuthToken."""
        raise NotImplementedError
    
    def lookup_token(self):
        if not os.path.exists('token.data'): return None
        file = open('token.data', )
        token = pickle.load(file)
        file.close()
        return token

def main():
    if len(sys.argv) < 2:
        key = raw_input('key (OAuth): ')
    else:
        key = sys.argv[1]

    if len(sys.argv) < 3:
        secret = raw_input('secret (OAuth): ')
    else:
        secret = sys.argv[2]
        
    ## request for access token desktop application
    #api = API((key, secret), 'test', True, True)
    #api.oauth_datastore = DataStore()
    #url, token = api.fetch_for_authorize()
    #print "Please copy the link to authorize the application"
    #print url
    #pin = raw_input('Insert pin: ')
    #token.set_verifier(pin)
    #api.fetch_access_token(token)
    
    api = Stream((key, secret), 'test', True, True)
    api.oauth_datastore = DataStore()
    #print api.verify_credentials()
    #print api.public_timeline_get()
    #print api.home_timeline_get(count=2)
    #print api.friends_timeline_get(count=2)
    #print api.user_timeline_get(count=2)
    #print api.mentions_get(count=2)    
    #print api.retweeted_by_me_get(count=2)
    #print api.retweeted_of_me_get(count=2)
    #print api.retweeted_to_me_get(count=2)
    #print api.status_show(21017907772)
    #print api.status_update("testing status update with mtweets")    
    #print api.status_destroy(21037924303)    
    #print api.status_retweet(21037278048)    
    def show(line):
        print line
    print dir(api.sample(show))
    
main()
    