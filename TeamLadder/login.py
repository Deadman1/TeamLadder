from main import BaseHandler, sessions
from api import hitapi

import json


#This page follows the instructions at http://wiki.warlight.net/index.php/CLOT_Authentication
class LoginPage(BaseHandler):
    def get(self):
        #Cast token to long to ensure the only contain numerical digits (this is easy in python since longs can go to any size.   In other languages we might have to do more work here to avoid overflows since tokens can exceed 2^32)
        token = str(long(self.request.GET['token']))
        clotpass = self.request.GET['clotpass']
        
        apiret = json.loads(hitapi('/API/ValidateInviteToken', { 'Token':  token }))
        
        if clotpass != apiret['clotpass']:
            return self.redirect('/loginfailed')
        
        self.session_store = sessions.get_store(request=self.request)
        
        self.session['authenticatedtoken'] = token
        
        self.redirect('/' + self.request.GET['state'])