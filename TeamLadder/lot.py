from main import ndb, get_template, flatten
from games import Game
from teams import Team
from google.appengine.api import memcache

import logging


class LOT(ndb.Model):
    """LOT stands for Ladder or Tournament.  Think of it as a single ladder or tournament. 
    By creating multiple LOTs, you can run multiple ladders or tournaments, or even a mix, on the same website."""
    name = ndb.StringProperty(required=True)
    dateCreated = ndb.DateTimeProperty(auto_now_add=True)
    dateEnded = ndb.DateTimeProperty()
    teamsParticipating = ndb.IntegerProperty(repeated=True) #list of team IDs
    teamRanks = ndb.IntegerProperty(repeated=True) #List of team IDs, in order by rank (first is first place, etc.)    
    teamRating = ndb.PickleProperty() #Dictionary of team IDs mapped to their TrueSkill rating
    teamMean = ndb.PickleProperty()
    teamStandardDeviation = ndb.PickleProperty() 
    customProperties = ndb.PickleProperty() # Dictionary to store custom properties about the lot

    def hasEnded(self):
        return self.dateEnded is not None


class LOTContainer():
    """LOTContainer contains a LOT instance alongside games (list) and players (dictionary of player ID to player)
    This class is cached.  Retrieve it using the getLot function.
    We have to make a container instead of just sticking the games and players into the LOT object.  I think this has
    to do with special pickle logic in ndb.Model that prevents extra data from pickeling"""
    lot = None
    games = None
    teams = None
    
    def render(self, pageName):
        #Before we render, sort team
        self.teamsSorted = list(self.teams.values())
        self.teamsSorted.sort(key=lambda t: self.lot.teamRanks.index(t.key.id()) if t.key.id() in self.lot.teamRanks else 999999)
        
        return get_template(pageName).render({'container': self })
    
    def teamRankOrBlank(self, teamID):
        if teamID not in self.lot.teamRanks:
            return ""
        else:
            return self.lot.teamRanks.index(teamID)+1
    
    
    def changed(self):
        """Call this after you update a LOT instance and it's games.  This will refresh the cache"""
        memcache.delete('lot_' + str(self.lot.key.id()), 5)
        for game in self.games:
            memcache.delete(str(game.key.id()), 5)
        
            
    def getFinishedGames(self):
        if self.games == None:
            return []
        return [game for game in self.games if game.dateEnded != None ]


def lotAddedOrRemoved():
    """Call this after you add or remove a LOT.  This will invalidate caches that retrieve lists of clots."""
    memcache.delete('home', 5)

    
def getLot(lotID):
    if isinstance(lotID, basestring):
        lotID = long(lotID)
    if isinstance(lotID, long):
        lotID = ndb.Key(LOT, lotID)
    
    key = 'lot_' + str(lotID.id())
    cached = memcache.get(key)
    if cached is not None:
        return cached
    
    container = retrieveLot(lotID)
    if not memcache.add(key, container, 300):
        logging.info("Memcache add failed")
    return container


def retrieveLot(lotID):
    lot = lotID.get()
    
    container = LOTContainer()
    container.lot = lot
    container.games = list(Game.query(Game.lotID == lotID.id()))
    
    #Load all teams that are referenced by the LOT.  First, get their team IDs and remove dupes
    tids = set(flatten([g.teams for g in container.games])) | set(lot.teamsParticipating) | set(lot.teamRanks)
    
    #Turn the team IDs into Team instances
    teams = list(ndb.get_multi([ndb.Key(Team, t) for t in tids]))
    
    #Store them as a dictionary so we can easily look them up by id later
    container.teams = dict([(t.key.id(), t) for t in teams if t is not None])
    
    return container