from api import hitapi, wlnet
from main import BaseHandler, addIfNotPresent, get_template
from players import Player

import logging
import json
import lot


class JoinPage(BaseHandler):
    def get(self, lotID):
        if 'authenticatedtoken' not in self.session:
            ############################################### SET TO main before going live ##################################
            # main - 5015900432
            # test - 314032996
            return self.redirect('http://' + wlnet + "/CLOT/Auth?p=314032996&state=join/" + str(long(lotID)))
        
        container = lot.getLot(lotID)
        inviteToken = self.session['authenticatedtoken']
        
        templates = [620619]
        templateIDs = ','.join(str(template) for template in templates)
        
        logging.info("current templates in use : " + templateIDs)
        
        #Call the warlight API to get the name, color, and verify that the invite token is correct
        tempapiret = hitapi('/API/ValidateInviteToken', { 'Token':  inviteToken, 'TemplateIDs': templateIDs})
        
        logging.info('tempapi return value' + str(tempapiret))
        logging.info("invite token = " + inviteToken)
        
        if (not "tokenIsValid" in tempapiret) or ("CannotUseTemplate" in tempapiret):
            return self.response.write('The supplied invite token is invalid.  Please contact the CLOT author for assistance.')
        
        #Check if this invite token is new to us
        player = Player.query(Player.inviteToken == inviteToken).get()
        
        
        data = json.loads(tempapiret)
        currentColor = data['color']
        currentName = data['name']
        if player is None:
            player = Player(inviteToken=inviteToken, name=currentName, color=currentColor, customProperties = {}, numberOfGamesAtOnce=5)
            player.put()
            logging.info("Created player " + unicode(player))
        else:
            # Update player details
            if currentColor != player.color:
                player.color = currentColor
            if currentName != player.name:
                player.name = currentName
            player.put()
            logging.info("Update player metadata for " + unicode(player))
            
        
        #Set them as participating in the current lot
        addIfNotPresent(container.lot.playersParticipating, player.key.id())
        container.players[player.key.id()] = player
        container.lot.put()
        container.changed()
        logging.info("Player " + unicode(player) + " joined " + unicode(container.lot))
        
        self.response.write(get_template('join.html').render({ 'container': container }))