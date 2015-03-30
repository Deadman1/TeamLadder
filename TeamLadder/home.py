from main import BaseHandler, get_template, getClotConfig
from google.appengine.api import memcache

import logging
import lot


class HomePage(BaseHandler):
    def get(self):
      
        cache = memcache.get('home')
        #if cache is not None:
        #    return self.response.write(cache)
        
        #Check if we need to do first-time setup
        if getClotConfig() is None:
            return self.redirect('/setup')
        
        html = get_template('home.html').render({ 'lots': list(lot.LOT.query()) })
        
        if not memcache.add('home', html):
            logging.info("Memcache add failed")
        
        self.response.write(html)
