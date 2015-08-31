from main import BaseHandler, get_template
from games import Game
from players import Player
from teams import Team
import lot


class TeamPage(BaseHandler):
    def get(self, teamID, lotID):
        teamID = long(teamID)
        team = Team.get_by_id(teamID)
        teamPlayers = [Player.get_by_id(pId) for pId in team.players]        
        
        games = Game.query(Game.teams == teamID)
        container = lot.getLot(lotID)
        
        currentTeam = None
        if 'authenticatedtoken' in self.session:
            inviteToken = self.session['authenticatedtoken']
            currentPlayer = Player.query(Player.inviteToken == inviteToken).get()
            if currentPlayer.activeTeam is not None:
                currentTeam = Team.get_by_id(currentPlayer.activeTeam)
        
        self.response.write(get_template('viewteam.html').render({'team': team, 'teamPlayers' : teamPlayers, 'games': games, 'currentTeam': currentTeam, 'container':container}))