from main import BaseHandler

import logging
import datetime
import lot


class FinishLotPage(BaseHandler):
    def get(self, lotID):
        container = lot.getLot(lotID)
        container.lot.dateEnded = datetime.datetime.now()
        container.lot.playersParticipating = []
        container.lot.put()
        container.changed()
    
        logging.info('LOT ended')
    
        self.redirect('/')


