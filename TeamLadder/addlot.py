from wtforms import Form, TextField, validators
from main import BaseHandler, get_template
import lot

class AddLotForm(Form):
    name = TextField("Name", [validators.required()])


class AddLotPage(BaseHandler):
    def get(self):
        self.response.write(get_template('addlot.html').render({ 'form': AddLotForm() }))


    def post(self):
        form = AddLotForm(self.request.POST)
        
        if not form.validate():
            return self.response.write("Please enter all fields")
        
        newlot = lot.LOT(name = form.name.data)
        newlot.playerRating = { } #empty dictionary
        newlot.playerMean = { } #empty dictionary
        newlot.playerStandardDeviation = { } #empty dictionary
        newlot.customProperties = { } #empty dictionary
        newlot.put()
        lot.lotAddedOrRemoved()
        
        self.redirect('/')