from api import hitapi, wlnet
from main import BaseHandler, get_template, addIfNotPresent
from players import Player
from teams import Team

import logging
import json
import lot

class JoinBase(BaseHandler):
    def renderPage(self, lotId, createTeamMessage = None, activateTeamMessage = None):
        if 'authenticatedtoken' not in self.session:
            ############################################### SET TO main before going live ##################################
            # main - 5015900432
            # test - 314032996
            return self.redirect('http://' + wlnet + "/CLOT/Auth?p=2428496679&state=join/" + str(long(lotId)))
        
        container = lot.getLot(lotId)
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
       
        try:
            playerTeams = [Team._get_by_id(tId) for tId in player.teams]
            candidateTeams = Team.query(Team.isCompleted == False).fetch()
            allTeams = []
            for team in candidateTeams:
                if(player.key.id() in team.players):
                    continue
                allTeams.append(team)
        except:
            playerTeams = []
            allTeams = []
       
        self.response.write(get_template('join.html').render({ 'container': container, 
            'player' : player, 'myTeams' : playerTeams, 'allTeams' : allTeams, 
            'createTeamMessage' : createTeamMessage, 'activateTeamMessage' : activateTeamMessage}))
        
    def getPlayer(self, lotId):
        #check if this player is known. Else don't let them create a team.
        if 'authenticatedtoken' not in self.session:
            ############################################### SET TO main before going live ##################################
            # main - 5015900432
            # test - 314032996
            return self.redirect('http://' + wlnet + "/CLOT/Auth?p=2428496679&state=join/" + str(long(lotId)))
        
        inviteToken = self.session['authenticatedtoken']
        player = Player.query(Player.inviteToken == inviteToken).get()
        
        return player
       
class JoinPage(JoinBase):
    def get(self, lotId):
        self.renderPage(lotId)
        
class CreateTeam(JoinBase):
    def get(self, lotId):
        player = self.getPlayer(lotId)
         
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
                player.totalTeams += 1
                player.put()
                logging.info("Created team " + unicode(team))
                message = "Team created successfully"
                 
        self.renderPage(lotId, createTeamMessage=message)
       
class ActivateTeam(JoinBase):
    def activateTeam(self, team, lotId):
        if team is None:
            return
        
        if team.isCompleted:
            teamMates = [Player.get_by_id(pId) for pId in team.players]
            teamActiveStatus = True
            for teamMate in teamMates:
                if teamMate.activeTeam != team.key.id():
                    teamActiveStatus = False
                    break                
            team.isActive = teamActiveStatus
            team.put()
            
            container = lot.getLot(lotId)
            
            #Set them as participating in the current lot
            addIfNotPresent(container.lot.teamsParticipating, team.key.id())
            container.teams[team.key.id()] = team
            container.lot.put()
            container.changed()
            logging.info("Team " + unicode(team) + " joined " + unicode(container.lot))
    
    def get(self, lotId, teamId):
        player = self.getPlayer(lotId)
        
        teamId = int(teamId)
        team = Team.get_by_id(teamId)        
        
        activateTeamMessage = "Failed to make active."
        if player is not None:        
            previousActiveTeamId = player.activeTeam
            if previousActiveTeamId is not None:
                previousActiveTeam = Team.get_by_id(previousActiveTeamId)
                previousActiveTeam.isActive = False
                previousActiveTeam.put()            
                     
            player.activeTeam = teamId
            self.activateTeam(team, lotId)                    
            player.put()
            activateTeamMessage = "Success!"
        
        self.renderPage(lotId, activateTeamMessage=activateTeamMessage)
        
class JoinTeam(JoinBase):
    def get(self, lotId, teamId):
        player = self.getPlayer(lotId)
        
        teamId = int(teamId)
        team = Team.get_by_id(teamId)        
        
        # Ban players who have created more than 10 teams
        if player is not None and team is not None and len(player.teams) < 3 and player.totalTeams < 10:                  
            if len(team.players) < 3:
                player.teams.append(teamId)
                player.totalTeams += 1
                team.players.append(player.key.id())
                team.name += " | " + player.name
                if len(team.players) ==3:
                    team.isCompleted = True
                player.put()
                team.put()
                
        self.renderPage(lotId)
        
class LeaveTeam(JoinBase):
    def get(self, lotId, teamId):
        player = self.getPlayer(lotId)
        
        teamId = int(teamId)
        team = Team.get_by_id(teamId)
        
        if player is not None and team is not None:
            teamPlayers = [Player.get_by_id(pId) for pId in team.players]
            for player in teamPlayers:
                if player.activeTeam == teamId:
                    player.activeTeam = None
                player.teams.remove(teamId)                
                player.put()
            
            
            #When they leave, remove them from this lot
            container = lot.getLot(lotId)
            
            if team.key.id() in container.lot.teamsParticipating:
                container.lot.teamsParticipating.remove(team.key.id())
                container.lot.put()
                container.changed()
                logging.info("Team left LOT " + unicode(team))
        
            team.key.delete()
            
        self.renderPage(lotId)