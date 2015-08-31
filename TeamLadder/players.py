from google.appengine.ext import ndb


class Player(ndb.Model):
    name = ndb.StringProperty()
    inviteToken = ndb.StringProperty(required=True)
    color = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    customProperties = ndb.PickleProperty() # empty dict to store custom properties for a player
    teams = ndb.IntegerProperty(repeated=True)
    activeTeam = ndb.IntegerProperty()
    
    # Total teams this player has been part of. Ban players who try to game the system by starting fresh runs    
    totalTeams = ndb.IntegerProperty(default=0) 
    

    def __repr__(self):
        return str(self.key.id()) + " " + self.name