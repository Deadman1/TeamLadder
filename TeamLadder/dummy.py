import json

ret = """{
  "termsOfUse" : "Please use this data feed responsibly, as it can consume significant amounts of server resources if called repeatedly.  After getting the data for a game, please store the data locally so you don't need to retrieve it from the WarLight server again.  The format of this data feed may change in the future.  The feed requires that you be signed into your member WarLight account to use.  If you're trying to access it programmatically, you may POST your username and API Token to this page in the format Email=your@email.com&APIToken=token",
  "id" : "8254948",
  "state" : "WaitingForPlayers",
  "name" : "Randomized ladder : Beren Erchamion vs M...",
  "numberOfTurns" : "-1",
  "templateID" : "620619",
  "players" : [ {
    "id" : "314032996",
    "name" : "Beren Erchamion",
    "email" : "...@...",
    "isAI" : "False",
    "color" : "#008000",
    "state" : "Playing"
  }, {
    "id" : "2428496679",
    "name" : "Master of the Dead",
    "email" : "...@...",
    "isAI" : "False",
    "color" : "NotYetDecided",
    "state" : "Declined"
  } ]
}"""

data = json.loads(ret)
state = data.get('state', 'err')
players = data.get('players', 'err')

for p in players:
    playerState = p.get('state')
    playerName = p.get('name')
    print playerName + ' - ' + playerState



    