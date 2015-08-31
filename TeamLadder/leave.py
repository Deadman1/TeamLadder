from main import BaseHandler, get_template
from players import Player
from api import wlnet
from teams import Team

import logging
import lot


class LeavePage(BaseHandler):
    def get(self, lotID):
        if 'authenticatedtoken' not in self.session:
            return self.redirect('http://' + wlnet + "/CLOT/Auth?p=2428496679&state=leave/" + str(long(lotID)))
        
        container = lot.getLot(lotID)
        inviteToken = self.session['authenticatedtoken']
        
        #Find the player by their token
        player = Player.query(Player.inviteToken == inviteToken).get()
        if not player:
            return self.response.write("Invite token is invalid.  Please contact the CLOT author for assistance.")
        
        #When they leave, remove their active team from this lot
        if player.activeTeam is not None:  
            team = Team.get_by_id(player.activeTeam)      
            if team.key.id() in container.lot.teamsParticipating:
                container.lot.teamsParticipating.remove(team.key.id())
                container.lot.put()
                container.changed()
                logging.info("Player left LOT " + unicode(player))
                logging.info("Removed team " + unicode(team))
        
        self.response.write(get_template('leave.html').render({ 'container': container }))