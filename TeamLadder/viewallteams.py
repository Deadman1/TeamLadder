from main import BaseHandler, get_template
import lot

class ViewAllTeamsPage(BaseHandler):
    def get(self, lotID):
        container = lot.getLot(lotID)
        self.response.write(get_template('viewallteams.html').render({'container': container, 'teamsrendered': container.render('renderallteams.html') }))

