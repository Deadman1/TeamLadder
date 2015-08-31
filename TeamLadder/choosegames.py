from main import BaseHandler
import lot
from players import Player
from teams import Team

class ChooseGamesPage(BaseHandler):
    def get(self, teamID, lotID, numberOfGames):
        teamID = long(teamID)
        
        if 'authenticatedtoken' not in self.session:
            return self.redirect('/')
        
        inviteToken = self.session['authenticatedtoken']
        player = Player.query(Player.inviteToken == inviteToken).get()
        
        if player.activeTeam != teamID :
            ''' Not the logged in user'''
            return self.redirect('/lot/'+ lotID)
        
        container = lot.getLot(lotID)
        team = Team.get_by_id(teamID)       
        
        if numberOfGames != None:
            team.numberOfGamesAtOnce = int(numberOfGames)
            team.put()
            container.teams[team.key.id()] = team            
            container.changed()
        
        self.redirect('/team/teamId=' + str(teamID) + '&&lotId=' + lotID)