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
from teams import Team

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
            ndb.delete_multi([o.key for o in Player.query()])
            ndb.delete_multi([o.key for o in Team.query()])            
            container.lot.teamRanks = []
            container.lot.teamRating = {}
            container.lot.teamMean = {}
            container.lot.teamStandardDeviation = {}
            container.lot.teamsParticipating = []
            container.lot.put()
            container.changed()
            memcache.flush_all()
            TestPage.renderPage(self, lotID, 'Deleted all games')        
        elif 'RunCron' in self.request.POST:
            #Just execute the same thing that we'd do if we hit /cron, but also time it
            start = datetime.now()
            cron.execute(self.request, container)
            TestPage.renderPage(self, lotID, 'Cron finished in ' + unicode(datetime.now() - start))        
        elif 'AddTeams' in self.request.POST:
            #Add some dummy team data. It won't work on warlight.net of course, but if TestMode is enabled it won't ever be passed there.   Just be sure and delete it before disabling TestMode.
            numTeams = long(self.request.POST["NumTeams"])
            
            for z in range(numTeams):                
                players = []
                for i in range(0,2):
                    name = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(5))                
                    p = Player(name=name, inviteToken=name, color="#0000FF", customProperties = {})
                    p.teams=[]
                    p.put()
                    players.append(p)
                    
                teamName = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(5))  
                team = Team(name = teamName, customProperties = {}, numberOfGamesAtOnce=3, 
                            teamLeader= players[0].key.id())
                team.put()
                
                
                for player in players:
                    team.players.append(player.key.id())
                    player.teams.append(team.key.id())
                    player.totalTeams += 1
                    player.put()
                
                team.put()
                
                container.lot.teamsParticipating.append(team.key.id())
            
            container.lot.put()
            container.changed()
            TestPage.renderPage(self, lotID, 'Added ' + str(numTeams) + ' fake teams')        
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