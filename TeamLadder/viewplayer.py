from main import BaseHandler, get_template
from games import Game
from players import Player
import lot


class PlayerPage(BaseHandler):
    def get(self, playerID, lotID):
        playerID = long(playerID)
        p = Player.get_by_id(playerID)
        games = Game.query(Game.players == playerID)
        container = lot.getLot(lotID)
        
        currentPlayer = None
        if 'authenticatedtoken' in self.session:
            inviteToken = self.session['authenticatedtoken']
            currentPlayer = Player.query(Player.inviteToken == inviteToken).get()
        
        self.response.write(get_template('viewplayer.html').render({'player': p, 'games': games, 'currentPlayer': currentPlayer, 'container':container}))