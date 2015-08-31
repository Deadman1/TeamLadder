import webapp2

from setup import SetupPage
from home import HomePage
from teamAdministration import JoinPage, CreateTeam, ActivateTeam, JoinTeam, LeaveTeam
from viewteam import TeamPage
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
    ("/teamAdministration/lotId=(\d+)", JoinPage),    
    ('/createTeam/lotId=(\d+)', CreateTeam),
    ('/activateTeam/lotId=(\d+)&&teamId=(\d+)', ActivateTeam),
    ('/joinTeam/lotId=(\d+)&&teamId=(\d+)', JoinTeam),
    ('/leaveTeam/lotId=(\d+)&&teamId=(\d+)', LeaveTeam),    
    ('/leave/lotId=(\d+)', LeavePage),
    ('/team/teamId=(\d+)&&lotId=(\d+)', TeamPage),
    ('/cron', CronPage),
    ('/test/(\d+)', TestPage),
    ('/addlot', AddLotPage),
    ('/lot/(\d+)', ViewLotPage),
    ('/login', LoginPage),
    ('/finishlot/(\d+)', FinishLotPage),
    ('/allteams/(\d+)', ViewAllTeamsPage),
    ('/choice/teamId=(\d+)&&lotId=(\d+)&&numberOfGames=(\d+)', ChooseGamesPage)
], debug=True, config=config)