from main import BaseHandler, get_template
from players import Player
from teams import Team
import lot


class ViewLotPage(BaseHandler):
    def get(self, lotID):
        currentTeam = None
        if 'authenticatedtoken' in self.session:
            inviteToken = self.session['authenticatedtoken']
            currentPlayer = Player.query(Player.inviteToken == inviteToken).get()
            if currentPlayer.activeTeam is not None:
                currentTeam = Team.get_by_id(currentPlayer.activeTeam)
        
        container = lot.getLot(lotID)
        self.response.write(get_template('viewlot.html').render({'container': container, 'currentTeam': currentTeam, 'lotrendered': container.render('renderlot.html') }))