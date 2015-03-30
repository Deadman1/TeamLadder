from main import BaseHandler, get_template
from players import Player
import lot


class ViewLotPage(BaseHandler):
    def get(self, lotID):
        currentPlayer = None
        if 'authenticatedtoken' in self.session:
            inviteToken = self.session['authenticatedtoken']
            currentPlayer = Player.query(Player.inviteToken == inviteToken).get()
        
        container = lot.getLot(lotID)
        self.response.write(get_template('viewlot.html').render({'container': container, 'currentPlayer': currentPlayer, 'lotrendered': container.render('renderlot.html') }))