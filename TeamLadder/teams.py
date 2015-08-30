from google.appengine.ext import ndb

class Team(ndb.Model):
    name = ndb.StringProperty()    
    created = ndb.DateTimeProperty(auto_now_add=True)
    customProperties = ndb.PickleProperty() # empty dict to store custom properties for a team
    numberOfGamesAtOnce = ndb.IntegerProperty()
    players = ndb.IntegerProperty(repeated=True) #list of player IDs in the team
    teamLeader = ndb.IntegerProperty()
    

    def __repr__(self):
        return str(self.key.id()) + ", Name = " + self.name +", Players" + str(self.players)