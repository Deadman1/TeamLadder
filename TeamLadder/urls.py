import webapp2

from setup import SetupPage
from home import HomePage
from join import JoinPage, CreateTeam
from viewplayer import PlayerPage
from leave import LeavePage
from cron import CronPage
from test import TestPage
from viewlot import ViewLotPage
from addlot import AddLotPage
from login import LoginPage
from finishlot import FinishLotPage
from viewallteams import ViewAllTeamsPage
from choosegames import ChooseGamesPage

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'VxZwg0oAiZPJ6gqaF1Nb',
}


application = webapp2.WSGIApplication([
    ('/', HomePage),
    ('/setup', SetupPage),
    ('/join/lotId=(\d+)', JoinPage),
    ('/createteam/lotId=(\d+)', CreateTeam),
    ('/leave/(\d+)', LeavePage),
    ('/player/playerId=(\d+)&&lotId=(\d+)', PlayerPage),
    ('/cron', CronPage),
    ('/test/(\d+)', TestPage),
    ('/addlot', AddLotPage),
    ('/lot/(\d+)', ViewLotPage),
    ('/login', LoginPage),
    ('/finishlot/(\d+)', FinishLotPage),
    ('/allteams/(\d+)', ViewAllTeamsPage),
    ('/choice/playerId=(\d+)&&lotId=(\d+)&&numberOfGames=(\d+)', ChooseGamesPage)
], debug=True, config=config)