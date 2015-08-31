from google.appengine.ext import ndb

import json
import urlparse
import logging


class Game(ndb.Model):
    """Represents a game.  This has its own ID local to the CLOT, but it also stores wlnetGameID which is the ID of the game on WarLight.net.
    This also stores a winner field which contains a teamID only if the game is finished.
    The __repr__ function is just used for debugging."""
    
    lotID = ndb.IntegerProperty(required=True, indexed=True)
    teams = ndb.IntegerProperty(repeated=True)
    winner = ndb.IntegerProperty()
    wlnetGameID = ndb.IntegerProperty(required=True, indexed=True)
    name = ndb.StringProperty()
    dateCreated = ndb.DateTimeProperty(auto_now_add=True)
    dateEnded = ndb.DateTimeProperty()
    deleted = ndb.BooleanProperty(default=False) #Set to true if this game was deleted over on WarLight.
    HasRatingChangedDueToResult = ndb.BooleanProperty(default=False) #Set to true once rating/ranks on the ladder are updated, according to the result 

    def __repr__(self):
        return str(self.key.id()) + ", wlnetGameID=" + str(self.wlnetGameID) + ", players=" + unicode(self.teams)


def createGame(request, container, teams, templateID):
    """This calls the WarLight.net API to create a game, and then creates the Game rows in the local DB"""
    gameName = '3v3 ladder : ' +  ' vs '.join([t.name for t in teams])
    gameName = gameName[:40] + "..."
    
    config = getClotConfig()
    
    if( teams is None or len(teams) !=2) :
        return
    
    players = []
    for team in teams:
        for pId in team.players:
            player = Player.get_by_id(pId)
            players.append({'token': player.inviteToken, 'team': team.key.id()})
    
    apiRetStr = postToApi('/API/CreateGame', json.dumps( { 
                                 'hostEmail': config.adminEmail, 
                                 'hostAPIToken': config.adminApiToken,
                                 'templateID': templateID,
                                 'gameName': gameName,
                                 'personalMessage': 'Created by the CLOT at http://' + urlparse.urlparse(request.url).netloc,
                                 'players': players
                                 }))
    apiRet = json.loads(apiRetStr)
    
    gid = long(apiRet.get('gameID', -1))
    if gid == -1:
        raise Exception("CreateGame returned error: " + apiRet.get('error', apiRetStr))
    
    g = Game(lotID=container.lot.key.id(), wlnetGameID=gid, name=gameName)
    g.teams = [t.key.id() for t in teams]
    g.put()
    
    #Ensure we update the container with the new game.  The players may already be there, but put them in in case they're not
    container.games.append(g)
    for t in teams:
        container.teams[t.key.id()] = t
    
    logging.info("Created game " + str(g.key.id()) + " '" + gameName + "', wlnetGameID=" + str(gid) + "', TemplateID=" + str(templateID))
    
    return g


from api import postToApi
from main import getClotConfig
from players import Player