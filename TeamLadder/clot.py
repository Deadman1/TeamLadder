from games import createGame
from main import flatten

import ConfigParser
import logging
from random import choice, randrange
import os.path
from datetime import datetime
from TrueSkill.trueskill import Rating, rate_1vs1
import operator
from itertools import islice


#The template ID defines the settings used when the game is created.  You can create your own template on warlight.net and enter its ID here
templates = [620619]
timeBetweenGamesInHours = 1
InitialMean = 2000.0
InitialStandardDeviation = 200.0


def createGames(request, container):
    """This is called periodically to check for new games that need to be created.  
    You should replace this with your own logic for how games are to be created.
    Right now, this function just randomly pairs up players who aren't in a game."""
    
    # Read configuration settings for ladder
    readConfigForMDLadder()
    
    #Recent games. All players who have played each other recently, will not be paired together.
    recentGames = []
    for g in container.games:
        delta = (datetime.now() - g.dateCreated)
        timeElapsed = delta.total_seconds()        
        if int(timeElapsed) <  timeBetweenGamesInHours * 60 * 60 :
            recentGames.append(g)
    
    #Retrieve all games that are ongoing
    activeGames = [g for g in container.games if g.winner is None]
    activeGameIDs = dict([[g.key.id(), g] for g in activeGames])
    logging.info("Active games: " + unicode(activeGameIDs))
    
    #Throw all of the player IDs that are in these ongoing games into a list
    playerIDsInActiveGames = flatten([g.players for g in activeGames])
    
    # Map of {player:gameCount}
    activeGameCountForPlayer = {}
    for p in playerIDsInActiveGames:        
        activeGameCountForPlayer[p] = activeGameCountForPlayer.get(p, 0) + 1
    
    # Map of {player:NumOfGamesToBeAllotted}     
    playersToBeAllocatedNewGames = {}
    for p in container.lot.playersParticipating:
        player = container.players[p]
        newGames = player.numberOfGamesAtOnce - activeGameCountForPlayer.get(p, 0)
        playersToBeAllocatedNewGames[p] = newGames
        
    logging.info("Games to be allotted: " + str(playersToBeAllocatedNewGames))
    
    #Create a game for everyone not in a game.
    #From a list of templates, a random one is picked for each game
    gamesCreated = []
    for pair in createPlayerPairs(container.lot.playerRanks, playersToBeAllocatedNewGames, recentGames):
        chosenTemplateId = int(choice(templates))
        overriddenBonuses = getOverriddenBonuses(chosenTemplateId)
        players = [container.players[p] for p in pair]
        g = createGame(request, container, players, chosenTemplateId, overriddenBonuses)
        gamesCreated.append(g)
        
        logging.info("Overridden Bonuses for game " + unicode(g) + " : " + str(overriddenBonuses))
        
    logging.info("Created games " + unicode(','.join([unicode(g) for g in gamesCreated])))


def setRanks(container):
    """This looks at what games everyone has won and sets their currentRank field.
    The current algorithm is very simple - just award ranks based on number of games won.
    You should replace this with your own ranking logic."""
    
    #Load all finished games which haven't been considered in the ranking
    finishedGames = [g for g in container.games if g.winner != None and g.HasRatingChangedDueToResult ==False]
    
    #update ratings in the container object
    updateRatingBasedOnRecentFinsihedGames(finishedGames, container)
    
    #Map this from Player.query() to ensure we have an entry for every player, even those with no wins(assign default rating if none exists)
    playersMappedToRating = {}
    playersMappedToMean = {}
    playersMappedToStandardDeviation = {}
    
    for p in container.players.values():
        playersMappedToRating[p.key.id()] = container.lot.playerRating.get(p.key.id(), computeRating(InitialMean, InitialStandardDeviation))
        playersMappedToMean[p.key.id()] = container.lot.playerMean.get(p.key.id(), InitialMean)
        playersMappedToStandardDeviation[p.key.id()] = container.lot.playerStandardDeviation.get(p.key.id(), InitialStandardDeviation)    
       
    #sort by player rating.
    sortedPlayersByRating = sorted(playersMappedToRating.items(), key=operator.itemgetter(1), reverse=True)
    
    #Store the player IDs back into the LOT object
    container.lot.playerRanks = [p[0] for p in sortedPlayersByRating]
    container.lot.playerMean = playersMappedToMean
    container.lot.playerStandardDeviation = playersMappedToStandardDeviation
    container.lot.playerRating = playersMappedToRating
    
    allGames = [g for g in container.games]
    
    # Set all finished games' HasRatingChangedDueToResult flag to true
    for game in allGames:
        if game.winner != None:
            game.HasRatingChangedDueToResult = True
        
    container.games = allGames    
    
    logging.info('setRanks finished')


def gameFailedToStart(elapsed):
    """This is called for games that are in the lobby.  We should determine if the game failed to
    start or not based on how long it's been in the lobby"""
    return elapsed.days >= 3


""" This method creates pairs between players, so that games can be created for each pair.
For a player with rank r, the algorithm creates a pair randomly with another player between rank r-10 to r+10.
It begins from rank 1, and picks a player till rank 10. It recurses till the bottom most rank looking at the next 10 players every time.
Since a player got considered when the person 10 ranks above him was getting an opponent, r-10 to r+10 all are possible candidates.
There is also a restriction that players who have played each other recently cannot play each other.
"""
def createPlayerPairs(completePlayerListSortedByRank, playersToBeAllocatedNewGamesMap, recentGames):
    eligiblePlayersSortedByRank = []
    for player in completePlayerListSortedByRank:
        for p in playersToBeAllocatedNewGamesMap.keys():
            if player == p:
                eligiblePlayersSortedByRank.append(p)
    
    # Dict containing each player as key, and list of players they have played as value
    # {p1:[p2,p3]}
    recentMatchups = {}
    
    for game in recentGames:
        p1 = game.players[0]
        p2 = game.players[1]
        
        recentMatchups.setdefault(p1, set()).add(p2)
        recentMatchups.setdefault(p2, set()).add(p1)
    
    """ Groups the list of players into pairs.  
    However if the two players in a pair have played each other recently, then a different pair is formed"""
    numOfPlayers = len(eligiblePlayersSortedByRank)
    
    # Pairs of players to be returned
    playerPairs = []
    
    for i in range(1, numOfPlayers):
        firstPlayer = eligiblePlayersSortedByRank[i-1]

        # find possible opponents with a similar rank(currently 10 above or 10 below)
        start = max(0, i-10)
        possibleOpponents = list(islice(eligiblePlayersSortedByRank, start, i+10))
        
        # player cannot play himself
        possibleOpponents.remove(firstPlayer)
        
        eligibleOpponents = list(possibleOpponents)
        for opponent in possibleOpponents:
            # opponent has already been allotted max number of games.
            if playersToBeAllocatedNewGamesMap[opponent] == 0:
                eligibleOpponents.remove(opponent)
                continue
        
            # They have already played recently    
            if recentMatchups != None and firstPlayer in recentMatchups.keys() and opponent in recentMatchups[firstPlayer]:                
                eligibleOpponents.remove(opponent)
                continue
        
        # Find opponents till no more games are to be allocated for this player
        while playersToBeAllocatedNewGamesMap[firstPlayer] != 0:                
            if len(eligibleOpponents) ==0:
                # No suitable opponent found
                break    
            
            # randomly pick the opponent 
            secPlayer = choice(eligibleOpponents)
            
            playersToBeAllocatedNewGamesMap[firstPlayer] = playersToBeAllocatedNewGamesMap[firstPlayer] - 1
            playersToBeAllocatedNewGamesMap[secPlayer] = playersToBeAllocatedNewGamesMap[secPlayer] - 1
            
            playerPairs.append([firstPlayer, secPlayer])
            
            # remove secPlayer as possible opponent for further game allocations
            eligibleOpponents.remove(secPlayer)
            
            
            # also add this to recent matchups
            recentMatchups.setdefault(firstPlayer, set()).add(secPlayer)
            recentMatchups.setdefault(secPlayer, set()).add(firstPlayer)
            
    return playerPairs


"""Reads configuration for MD ladder"""
def readConfigForMDLadder():
    cfgFile = os.path.dirname(__file__) + '/config/Ladder.cfg'
    Config = ConfigParser.ConfigParser()
    Config.read(cfgFile)
    
    # declare as global variables
    global templates
    global timeBetweenGamesInHours
    global InitialMean
    global InitialStandardDeviation
    
    try:
        allTemplates = Config.get("MDLadder", "templates")
        delimiter = Config.get("MDLadder","delimiter")
        templates = allTemplates.split(delimiter)
        timeBetweenGamesInHours = int(Config.get("MDLadder", "timeBetweenGamesInHours"))
        InitialMean = float(Config.get("MDLadder", "initialMean"))
        InitialStandardDeviation = float(Config.get("MDLadder", "initialStandardDeviation"))
    except:
        raise Exception("Failed to load MD ladder config file")

""" Given a mean and a standardDeviation, the rating is calculated as """
def computeRating(mean, standardDeviation):
    return mean - standardDeviation * 3


def updateRatingBasedOnRecentFinsihedGames(finishedGamesGroupedByWinner, container):
    standardDeviationDict = container.lot.playerStandardDeviation
    meanDict = container.lot.playerMean
    ratingdict = container.lot.playerRating
    
    for game in finishedGamesGroupedByWinner:
        player1, player2 = game.players
        winnerId = game.winner
        loserId = None
        if winnerId == player1:
            loserId = player2
        else:
            loserId = player1
        
        winnerPreviousMean = meanDict.get(winnerId, InitialMean)
        winnerPreviousStandardDeviation = standardDeviationDict.get(winnerId, InitialStandardDeviation)
        loserPreviousMean = meanDict.get(loserId, InitialMean)
        loserPreviousStandardDeviation = standardDeviationDict.get(loserId, InitialStandardDeviation)
        
        winnerTrueSkillRating = Rating(winnerPreviousMean, winnerPreviousStandardDeviation)
        loserTrueSkillRating = Rating(loserPreviousMean, loserPreviousStandardDeviation)
        
        # Apply TrueSkill algorithm to compute new rating based on game outcome.
        winnerTrueSkillRating, loserTrueSkillRating = rate_1vs1(winnerTrueSkillRating, loserTrueSkillRating)
        
        #update the dicts
        meanDict[winnerId] = winnerTrueSkillRating.mu
        meanDict[loserId] = loserTrueSkillRating.mu
        standardDeviationDict[winnerId] = winnerTrueSkillRating.sigma
        standardDeviationDict[loserId] = loserTrueSkillRating.sigma
        
    # Once the mean,SD have been updated after considering all the games, compute the new Rating
    for playerID in meanDict.keys():
        ratingdict[playerID] = computeRating(meanDict[playerID], standardDeviationDict[playerID])
    
    container.lot.playerMean = meanDict
    container.lot.playerStandardDeviation = standardDeviationDict
    container.lot.playerRating = ratingdict
    
    logging.info('Ratings updated based on game results')    
    
    
def getOverriddenBonuses(templateId):
    if templateId != 620619:
        return None
    
    cfgFile = os.path.dirname(__file__) + '/config/BonusInfo/' + str(templateId) +'.values'
    Config = ConfigParser.ConfigParser()
    Config.optionxform = str   
    Config.read(cfgFile)
    
    try:        
        allBonuses = dict(Config.items('Bonuses'))
        for region in allBonuses.keys():
            bonusValue = int(allBonuses[region])
            
            # Set it to a new value of v-1 or v or v+1
            allBonuses[region] = randrange(bonusValue-1, bonusValue+2)
        
        overriddenBonuses = [{'bonusName' : region, 'value' : bonusValue} for region, bonusValue in allBonuses.iteritems()]
        logging.info(str(overriddenBonuses))    
        return overriddenBonuses
    except:
        raise Exception("Failed to load bonus config file for the template : " + str(templateId))