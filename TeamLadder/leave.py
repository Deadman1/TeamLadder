from main import BaseHandler, get_template
from players import Player
from api import wlnet

import logging
import lot


class LeavePage(BaseHandler):
    def get(self, lotID):
        if 'authenticatedtoken' not in self.session:
            return self.redirect('http://' + wlnet + "/CLOT/Auth?p=314032996&state=leave/" + str(long(lotID)))
        
        container = lot.getLot(lotID)
        inviteToken = self.session['authenticatedtoken']
        
        #Find the player by their token
        player = Player.query(Player.inviteToken == inviteToken).get()
        if not player:
            return self.response.write("Invite token is invalid.  Please contact the CLOT author for assistance.")
        
        #When they leave, remove them from this lot
        if player.key.id() in container.lot.playersParticipating:
            container.lot.playersParticipating.remove(player.key.id())
            container.lot.put()
            container.changed()
            logging.info("Player left LOT " + unicode(player))
        
        self.response.write(get_template('leave.html').render({ 'container': container }))