from api import hitapi, wlnet
from main import BaseHandler, addIfNotPresent, get_template
from players import Player
from teams import Team

import logging
import json
import lot


class JoinPage(BaseHandler):
    def get(self, lotID):
        if 'authenticatedtoken' not in self.session:
            ############################################### SET TO main before going live ##################################
            # main - 5015900432
            # test - 314032996
            return self.redirect('http://' + wlnet + "/CLOT/Auth?p=2428496679&state=join/" + str(long(lotID)))
        
        container = lot.getLot(lotID)
        inviteToken = self.session['authenticatedtoken']
        
        templates = [708081]
        templateIDs = ','.join(str(template) for template in templates)
        
        logging.info("current templates in use : " + templateIDs)
        
        #Call the warlight API to get the name, color, and verify that the invite token is correct
        tempapiret = hitapi('/API/ValidateInviteToken', { 'Token':  inviteToken, 'TemplateIDs': templateIDs})
        
        logging.info('tempapi return value' + str(tempapiret))
        logging.info("invite token = " + inviteToken)
        
        if (not "tokenIsValid" in tempapiret) or ("CannotUseTemplate" in tempapiret):
            return self.response.write('The supplied invite token is invalid. You may not have unlocked some Warlight features yet. Please contact the CLOT author for assistance.')
        
        #Check if this invite token is new to us
        player = Player.query(Player.inviteToken == inviteToken).get()
        
        
        data = json.loads(tempapiret)
        currentColor = data['color']
        currentName = data['name']
        if player is None:
            player = Player(inviteToken=inviteToken, name=currentName, color=currentColor, customProperties = {})
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
            
        teams = [Team._get_by_id(tId) for tId in player.teams]        
        
        self.response.write(get_template('join.html').render({ 'container': container, 'player' : player, 'teams' : teams }))
        
        
class CreateTeam(BaseHandler):
    def get(self, lotID):
        #check if this player is known. Else don't let them create a team.
        if 'authenticatedtoken' not in self.session:
            ############################################### SET TO main before going live ##################################
            # main - 5015900432
            # test - 314032996
            return self.redirect('http://' + wlnet + "/CLOT/Auth?p=2428496679&state=join/" + str(long(lotID)))
         
        container = lot.getLot(lotID)
        inviteToken = self.session['authenticatedtoken']
        player = Player.query(Player.inviteToken == inviteToken).get()
         
        message = None
        if player is not None:
            if player.teams is not None and len(player.teams) == 3:
                message = "Failed to add team. A player can be part of at most three teams."
            else:
                team = Team(name = player.name, customProperties = {}, numberOfGamesAtOnce=3, 
                            teamLeader= player.key.id())
                team.players = [player.key.id()]
                team.put()
                player.teams.append(team.key.id())
                player.put()
                logging.info("Created team " + unicode(team))
                message = "Team created successfully"
         
        teams = [Team._get_by_id(tId) for tId in player.teams]
        
        self.response.write(get_template('join.html').render({ 'container': container, 
                                                              'message' : message, 'player' : player, 'teams' : teams }))