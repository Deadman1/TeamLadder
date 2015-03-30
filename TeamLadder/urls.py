import webapp2

from setup import SetupPage
from home import HomePage
from join import JoinPage
from viewplayer import PlayerPage
from leave import LeavePage
from cron import CronPage
from test import TestPage
from viewlot import ViewLotPage
from addlot import AddLotPage
from login import LoginPage
from finishlot import FinishLotPage
from viewallplayers import ViewAllPlayersPage
from choosegames import ChooseGamesPage

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'VxZwg0oAiZPJ6gqaF1Nb',
}


application = webapp2.WSGIApplication([
    ('/', HomePage),
    ('/setup', SetupPage),
    ('/join/(\d+)', JoinPage),
    ('/leave/(\d+)', LeavePage),
    ('/player/playerId=(\d+)&&lotId=(\d+)', PlayerPage),
    ('/cron', CronPage),
    ('/test/(\d+)', TestPage),
    ('/addlot', AddLotPage),
    ('/lot/(\d+)', ViewLotPage),
    ('/login', LoginPage),
    ('/finishlot/(\d+)', FinishLotPage),
    ('/allplayers/(\d+)', ViewAllPlayersPage),
    ('/choice/playerId=(\d+)&&lotId=(\d+)&&numberOfGames=(\d+)', ChooseGamesPage)
], debug=True, config=config)