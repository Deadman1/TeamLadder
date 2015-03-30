from api import hitapi, postToApi
from main import BaseHandler, getClotConfig

import random
import datetime
import logging
import json
import clot
import lot


class CronPage(BaseHandler):
    def get(self):    
        for lotInst in lot.LOT.query():
            if not lotInst.hasEnded():
                execute(self.request, lot.getLot(lotInst.key))
        
        self.response.write("Cron complete")


def execute(request, container):
    logging.info("Starting cron for " + container.lot.name + "...")
    checkInProgressGames(container)    
    clot.setRanks(container)
    
    #Update the cache. We may not have changed anything, but we update it all of the time anyway. If we wanted to improve this we could set a dirty flag and check it here.
    container.lot.put()
    for game in container.games:
        game.put()
    container.changed()
    clot.createGames(request, container)
    
    logging.info("Cron done")


def checkInProgressGames(container):
    """This is called periodically to look for games that are finished.  If we find a finished game, we record the winner"""

    #Find all games that we think aren't finished
    activeGames = [g for g in container.games if g.winner is None]

    for g in activeGames:
        #call WarLight's GameFeed API so that it can tell us if it's finished or not
        apiret = hitapi('/API/GameFeed?GameID=' + str(g.wlnetGameID), {})
        data = json.loads(apiret)
        state = data.get('state', 'err')
        if state == 'err': raise Exception("GameFeed API failed.  Message = " + data.get('error', apiret))
        
        if state == 'Finished':        
            #It's finished. Record the winner and save it back.
            winner = findWinner(container, data)
            logging.info('Identified the winner of game ' + str(g.wlnetGameID) + ' is ' + unicode(winner))
            g.winner = winner.key.id()
            g.dateEnded = datetime.datetime.now()
            g.put()        
        elif state == 'WaitingForPlayers':
            #It's in the lobby still. Check if it's been too long.
            elapsed = datetime.datetime.now() - g.dateCreated
            players = data.get('players', 'err')
            if players == 'err' : raise Exception("GameFeed API failed.  Message = " + data.get('error', apiret))
            
            hasEitherPlayerDeclined = False
            for p in players:
                playerState = p.get('state', 'err')
                if playerState =='err' : raise Exception("GameFeed API failed.  Message = " + data.get('error', apiret)) 
                if playerState == 'Declined':
                    hasEitherPlayerDeclined = True
                    break
            
            if clot.gameFailedToStart(elapsed) or hasEitherPlayerDeclined == True:
                logging.info('Game ' + str(g.wlnetGameID) + " is stuck in the lobby. Marking it as a loss for anyone who didn't join and deleting it.")
            
                #Delete it over at warlight.net so that players know we no longer consider it a real game
                config = getClotConfig()
                deleteRet = postToApi('/API/DeleteLobbyGame', json.dumps( { 
                                             'Email': config.adminEmail, 
                                             'APIToken': config.adminApiToken,
                                             'gameID': g.wlnetGameID }))
                
                #If the API doesn't return success, just ignore this game on this run. This can happen if the game just started between when we checked its status and when we told it to delete.
                if 'success' not in deleteRet:
                    logging.info("DeleteLobbyGame did not return success. Ignoring this game for this run.  Return=" + deleteRet)
                else:
                    #We deleted the game.  Mark it as deleted and finished
                    g.deleted = True
                    g.winner = findWinnerOfDeletedGame(container, data).key.id()
                    g.put()
                    
                    #Also remove anyone that declines or fails to join from the ladder.  This is important for real-time ladders since we don't want idle people staying in forever, but you may not want this for your situation
                    for playerID in [getPlayerByInviteToken(container, p['id']).key.id() for p in data['players'] if p['state'] != 'Playing']:
                        if playerID in container.lot.playersParticipating:
                            container.lot.playersParticipating.remove(playerID)
                            logging.info("Removed " + str(playerID) + " from ladder since they did not join game " + str(g.wlnetGameID))    
            else :
                logging.info("Game " + str(g.wlnetGameID) + " is in the lobby for " + str(elapsed.days) + " days.")    
        else:
            #It's still going.
            logging.info('Game ' + str(g.wlnetGameID) + ' is not finished, state=' + state + ', numTurns=' + data['numberOfTurns'])


def findWinner(container, data):
    """Simple helper function to return the Player who won the game.  This takes json data returned by the GameFeed 
    API.  We just look for a player with the "won" state and then retrieve their Player instance from the database"""
    winners = filter(lambda p: p['state'] == 'Won', data['players'])
    if len(winners) == 0:
        #The only way there can be no winner is if the players VTE.  Just pick one at random, since the Game structure always assumes there's a winner.  Alternatively we could just delete the game.
        return getPlayerByInviteToken(container, random.choice(data['players'])["id"])
    else:
        return getPlayerByInviteToken(container, winners[0]["id"])


def findWinnerOfDeletedGame(container, data):
    """Simple helper function to return the Player who should be declared the winner of a game that never began.
    If it didn't begin, it's because someone either didn't join the game or declined it.  They'll be considered
    the loser, so whoever joined is the winner by default."""
    
    joined = filter(lambda p: p['state'] == 'Playing', data['players'])
    if len(joined) > 0:
        return getPlayerByInviteToken(container, random.choice(joined)["id"])
    
    """If everyone declined or failed to join, we just pick the winner randomly since the Game data structure 
    currently assumes there's always one winner."""
    return getPlayerByInviteToken(container, random.choice(data['players'])["id"])


def getPlayerByInviteToken(container, inviteToken):
    return [p for p in container.players.values() if p.inviteToken == inviteToken][0]
