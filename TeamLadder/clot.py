from games import createGame
from main import flatten
from random import choice

import ConfigParser
import logging
import os.path
from datetime import datetime
from TrueSkill.trueskill import Rating, rate_1vs1
import operator
from itertools import islice


#The template ID defines the settings used when the game is created.  You can create your own template on warlight.net and enter its ID here
template = 708081
timeBetweenGamesInHours = 1
InitialMean = 2000.0
InitialStandardDeviation = 200.0


def createGames(request, container):
    """This is called periodically to check for new games that need to be created.  
    You should replace this with your own logic for how games are to be created.
    Right now, this function just randomly pairs up players who aren't in a game."""
    
    # Read configuration settings for ladder
    readConfigForTeamLadder()
    
    #Recent games. All teams who have played each other recently, will not be paired together.
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
    
    #Throw all of the team IDs that are in these ongoing games into a list
    teamIDsInActiveGames = flatten([g.teams for g in activeGames])
    
    # Map of {team:gameCount}
    activeGameCountForTeam = {}
    for tId in teamIDsInActiveGames:        
        activeGameCountForTeam[tId] = activeGameCountForTeam.get(tId, 0) + 1
    
    # Map of {team:NumOfGamesToBeAllotted}     
    teamsToBeAllocatedNewGames = {}
    for t in container.lot.teamsParticipating:
        team = container.teams[t]
        newGames = team.numberOfGamesAtOnce - activeGameCountForTeam.get(t, 0)
        teamsToBeAllocatedNewGames[t] = newGames
        
    logging.info("Games to be allotted: " + str(teamsToBeAllocatedNewGames))
    
    #Create a game for every team not in a game.    
    gamesCreated = []
    for pair in createTeamPairs(container.lot.teamRanks, teamsToBeAllocatedNewGames, recentGames):
        teams = [container.teams[p] for p in pair]
        g = createGame(request, container, teams, template)
        gamesCreated.append(g)
        
    logging.info("Created games " + unicode(','.join([unicode(g) for g in gamesCreated])))


def setRanks(container):
    """This looks at what games everyone has won and sets their currentRank field.
    The current algorithm is very simple - just award ranks based on number of games won.
    You should replace this with your own ranking logic."""
    
    #Load all finished games which haven't been considered in the ranking
    finishedGames = [g for g in container.games if g.winner != None and g.HasRatingChangedDueToResult ==False]
    
    #update ratings in the container object
    updateRatingBasedOnRecentFinishedGames(finishedGames, container)
    
    #Map this from Player.query() to ensure we have an entry for every player, even those with no wins(assign default rating if none exists)
    teamsMappedToRating = {}
    teamsMappedToMean = {}
    teamsMappedToStandardDeviation = {}
    
    for t in container.teams.values():
        teamsMappedToRating[t.key.id()] = container.lot.teamRating.get(t.key.id(), computeRating(InitialMean, InitialStandardDeviation))
        teamsMappedToMean[t.key.id()] = container.lot.teamMean.get(t.key.id(), InitialMean)
        teamsMappedToStandardDeviation[t.key.id()] = container.lot.teamStandardDeviation.get(t.key.id(), InitialStandardDeviation)    
       
    #sort by team rating.
    sortedTeamsByRating = sorted(teamsMappedToRating.items(), key=operator.itemgetter(1), reverse=True)
    
    #Store the team IDs back into the LOT object
    container.lot.teamRanks = [t[0] for t in sortedTeamsByRating]
    container.lot.teamMean = teamsMappedToMean
    container.lot.teamStandardDeviation = teamsMappedToStandardDeviation
    container.lot.teamRating = teamsMappedToRating
    
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


""" This method creates pairs between teams, so that games can be created for each pair.
For a team with rank r, the algorithm creates a pair randomly with another team between rank r-10 to r+10.
It begins from rank 1, and picks a team till rank 10. It recurses till the bottom most rank looking at the next 10 teams every time.
Since a team got considered when the team 10 ranks above them was getting an opponent, r-10 to r+10 all are possible candidates.
There is also a restriction that teams who have played each other recently cannot play each other.
"""
def createTeamPairs(completeTeamListSortedByRank, teamsToBeAllocatedNewGamesMap, recentGames):
    eligibleTeamsSortedByRank = []
    for team in completeTeamListSortedByRank:
        for t in teamsToBeAllocatedNewGamesMap.keys():
            if team == t:
                eligibleTeamsSortedByRank.append(t)
    
    # Dict containing each team as key, and list of teams they have played as value
    # {t1:[t2,t3]}
    recentMatchups = {}
    
    for game in recentGames:
        t1 = game.teams[0]
        t2 = game.teams[1]
        
        recentMatchups.setdefault(t1, set()).add(t2)
        recentMatchups.setdefault(t2, set()).add(t1)
    
    """ Groups the list of teams into pairs.  
    However if the two teams in a pair have played each other recently, then a different pair is formed"""
    numOfTeams = len(eligibleTeamsSortedByRank)
    
    # Pairs of teams to be returned
    teamPairs = []
    
    for i in range(1, numOfTeams):
        firstTeam = eligibleTeamsSortedByRank[i-1]

        # find possible opponents with a similar rank(currently 10 above or 10 below)
        start = max(0, i-10)
        possibleOpponents = list(islice(eligibleTeamsSortedByRank, start, i+10))
        
        # team cannot play itself
        possibleOpponents.remove(firstTeam)
        
        eligibleOpponents = list(possibleOpponents)
        for opponent in possibleOpponents:
            # opponent has already been allotted max number of games.
            if teamsToBeAllocatedNewGamesMap[opponent] == 0:
                eligibleOpponents.remove(opponent)
                continue
        
            # They have already played recently    
            if recentMatchups != None and firstTeam in recentMatchups.keys() and opponent in recentMatchups[firstTeam]:                
                eligibleOpponents.remove(opponent)
                continue
        
        # Find opponents till no more games are to be allocated for this team
        while teamsToBeAllocatedNewGamesMap[firstTeam] != 0:                
            if len(eligibleOpponents) ==0:
                # No suitable opponent found
                break    
            
            # randomly pick the opponent 
            secTeam = choice(eligibleOpponents)
            
            teamsToBeAllocatedNewGamesMap[firstTeam] -= 1
            teamsToBeAllocatedNewGamesMap[secTeam] -= 1
            
            teamPairs.append([firstTeam, secTeam])
            
            # remove secTeam as possible opponent for further game allocations
            eligibleOpponents.remove(secTeam)
                        
            # also add this to recent match-ups
            recentMatchups.setdefault(firstTeam, set()).add(secTeam)
            recentMatchups.setdefault(secTeam, set()).add(firstTeam)
            
    return teamPairs


"""Reads configuration for MD ladder"""
def readConfigForTeamLadder():
    cfgFile = os.path.dirname(__file__) + '/config/Ladder.cfg'
    Config = ConfigParser.ConfigParser()
    Config.read(cfgFile)
    
    # declare as global variables
    global templates
    global timeBetweenGamesInHours
    global InitialMean
    global InitialStandardDeviation
    
    try:
        allTemplates = Config.get("TeamLadder", "templates")
        delimiter = Config.get("TeamLadder","delimiter")
        templates = allTemplates.split(delimiter)
        timeBetweenGamesInHours = int(Config.get("TeamLadder", "timeBetweenGamesInHours"))
        InitialMean = float(Config.get("TeamLadder", "initialMean"))
        InitialStandardDeviation = float(Config.get("TeamLadder", "initialStandardDeviation"))
    except:
        raise Exception("Failed to load Team ladder config file")

""" Given a mean and a standardDeviation, the rating is calculated as """
def computeRating(mean, standardDeviation):
    return mean - standardDeviation * 3


def updateRatingBasedOnRecentFinishedGames(finishedGamesGroupedByWinner, container):
    standardDeviationDict = container.lot.teamStandardDeviation
    meanDict = container.lot.teamMean
    ratingdict = container.lot.teamRating
    
    for game in finishedGamesGroupedByWinner:
        player1, player2 = game.teams
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
  
