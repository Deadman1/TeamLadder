from main import BaseHandler, get_template
import lot

class ViewAllPlayersPage(BaseHandler):
    def get(self, lotID):
        container = lot.getLot(lotID)
        self.response.write(get_template('viewallplayers.html').render({'container': container, 'playersrendered': container.render('renderallplayers.html') }))

