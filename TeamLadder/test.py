from google.appengine.api import memcache
from api import TestMode
from main import BaseHandler, get_template,ndb

from players import Player
from games import Game
from datetime import datetime
import cron
import random
import string
import lot

class TestPage(BaseHandler):
    def renderPage(self, lotID, message):
        container = lot.getLot(lotID)
        self.response.write(get_template('test.html').render({ 'container': container, 'renderedlot':  container.render('renderlot.html'), 'message': message }))
    
    
    def get(self, lotID):
        if not TestMode:
            return self.response.write("api.TestMode is not enabled.  This page should only be used while testing.")        
        TestPage.renderPage(self, lotID, '')
    
    
    def post(self, lotID):
        if not TestMode:
            return self.response.write("api.TestMode is not enabled.  This page should only be used while testing.")
        
        container = lot.getLot(lotID)
        
        if 'ClearData' in self.request.POST:
            #User clicked Clear Data, delete all games and players
            ndb.delete_multi([o.key for o in Game.query(Game.lotID == container.lot.key.id())])
            container.lot.playerRanks = []
            container.lot.playerRating = {}
            container.lot.playerMean = {}
            container.lot.playerStandardDeviation = {}
            container.lot.put()
            container.changed()
            memcache.flush_all()
            TestPage.renderPage(self, lotID, 'Deleted all games')        
        elif 'RunCron' in self.request.POST:
            #Just execute the same thing that we'd do if we hit /cron, but also time it
            start = datetime.now()
            cron.execute(self.request, container)
            TestPage.renderPage(self, lotID, 'Cron finished in ' + unicode(datetime.now() - start))        
        elif 'AddPlayers' in self.request.POST:
            #Add some dummy player data. It won't work on warlight.net of course, but if TestMode is enabled it won't ever be passed there.   Just be sure and delete it before disabling TestMode.
            numPlayers = long(self.request.POST["NumPlayers"])
            
            for z in range(numPlayers):
                name = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(5))
                p = Player(name=name, inviteToken=name, color="#0000FF", customProperties = {}, numberOfGamesAtOnce=2)
                p.put()
                container.lot.playersParticipating.append(p.key.id())
            
            container.lot.put()
            container.changed()
            TestPage.renderPage(self, lotID, 'Added ' + str(numPlayers) + ' fake players')        
        elif 'FlushCache' in self.request.POST:
            if memcache.flush_all():
                TestPage.renderPage(self, lotID, 'Deleted everything from cache')
            else:
                TestPage.renderPage(self, lotID, 'Error while trying to flush cache')        
        elif 'Test' in self.request.POST:
            #Just a blank space for testing random stuff  
            TestPage.renderPage(self, lotID, 'Ran test code')        
        else:
            self.response.write("No handler")   