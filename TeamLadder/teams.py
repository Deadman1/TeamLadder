from google.appengine.ext import ndb

class Team(ndb.Model):
    name = ndb.StringProperty()    
    created = ndb.DateTimeProperty(auto_now_add=True)
    customProperties = ndb.PickleProperty() # empty dict to store custom properties for a team
    numberOfGamesAtOnce = ndb.IntegerProperty()
    players = ndb.IntegerProperty(repeated=True) #list of player IDs in the team
    teamLeader = ndb.IntegerProperty()
    isCompleted = ndb.BooleanProperty(default=False) #Set to true if 3 players teamAdministration the team
    isActive = ndb.BooleanProperty(default=False) #Set to true if all three players on the team have this team as their active one.
    

    def __repr__(self):
        return str(self.key.id()) + ", Name = " + self.name +", Players" + str(self.players)