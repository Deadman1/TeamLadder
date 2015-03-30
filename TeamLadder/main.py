from google.appengine.ext import ndb
from webapp2_extras import sessions
from itertools import groupby

import os
import jinja2
import webapp2



JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


def get_template(name):
    return JINJA_ENVIRONMENT.get_template('templates/' + name)


class ClotConfig(ndb.Model):
    adminEmail = ndb.StringProperty(required=True)
    adminApiToken = ndb.StringProperty(required=True)


def getClotConfig():
    if api.TestMode:
        return ClotConfig(adminEmail='bogus', adminApiToken='bogus') #return a bogus one while we're in test mode. It'll never be used.
    
    #Use get_multi instead of get_by_id so that we return None if it doesn't exist. home.py uses this to tell if we're not setup yet
    return ndb.get_multi([ndb.Key(ClotConfig, 1)])[0]


def group(collection, keyfunc):
    data = sorted(collection, key=keyfunc)
    ret = {}
    for k,g in groupby(data, keyfunc):
        ret[k] = list(g)
    return ret


def flatten(listoflists):
    """Takes a list of lists and returns those items in a single list"""
    return [j for i in listoflists for j in i]

def addIfNotPresent(intputList, toAdd):
    if toAdd not in intputList:
        intputList.append(toAdd)


#from http://stackoverflow.com/questions/14078054/gae-webapp2-session-the-correct-process-of-creating-and-checking-sessions
class BaseHandler(webapp2.RequestHandler):              # taken from the webapp2 extrta session example
    def dispatch(self):                                 # override dispatch
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)       # dispatch the main handler
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


import api