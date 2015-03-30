from main import BaseHandler
import lot
from players import Player

class ChooseGamesPage(BaseHandler):
    def get(self, playerID, lotID, numberOfGames):
        playerID = long(playerID)
        
        if 'authenticatedtoken' not in self.session:
            return self.redirect('/')
        
        inviteToken = self.session['authenticatedtoken']
        player = Player.query(Player.inviteToken == inviteToken).get()
        
        if player.key.id() != playerID :
            ''' Not the logged in user'''
            return self.redirect('/lot/'+ lotID)
        
        container = lot.getLot(lotID) 
        
        if numberOfGames != None:
            player.numberOfGamesAtOnce = int(numberOfGames)
            player.put()
            container.players[player.key.id()] = player            
            container.changed()
        
        self.redirect('/player/playerId=' + str(playerID) + '&&lotId=' + lotID)