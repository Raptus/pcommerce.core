from persistent.mapping import PersistentMapping

from plone.memoize.instance import memoize

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.browser.components.base import BaseComponent
from pcommerce.core import PCommerceMessageFactory as _

class ShipmentsComponent(BaseComponent):
    template = ViewPageTemplateFile('shipments.pt')
    
    @property
    @memoize
    def selection(self):
        return dict([(value['products'], value['shipmentid']) for key, value in self.request.form.items() if key.startswith('shipment_id_') and value.has_key('shipmentid')])

    def validate(self):
        self.errors = {}
        valid = True
        for shipmentids, products in self._shipmentgroups().items():
            if len(shipmentids) > 1:
                key = tuple([p.UID() for p in products])
                if not self.selection.has_key(key):
                    self.errors[shipmentids] = _(u'Please select a shipment method.')
                    valid = False
                elif not self.selection[key] in shipmentids:
                    self.errors[shipmentids] = _(u'Please select a shipment method.')
                    valid = False
        return valid
    
    def process(self):
        self.order.shipmentids = PersistentMapping()
        for shipmentids, products in self._shipmentgroups().items():
            key = tuple([p.UID() for p in products])
            if len(shipmentids) > 1:
                shipmentid = self.selection[key]
            else:
                shipmentid = shipmentids[0]
            if not self.order.shipmentids.has_key(shipmentid):
                self.order.shipmentids[shipmentid] = ()
            self.order.shipmentids[shipmentid] = self.order.shipmentids[shipmentid] + key
    
    def renders(self):
        if len(self._shipments())==1:
            return False
        for shipments in self._shipmentgroups().keys():
            if len(shipments)>1:
                return True
        return False
    
    @property
    def multiple(self):
        shipmentsgroups = self._shipmentgroups()
        if len(shipmentsgroups) == 1:
            return False
        count = 0
        for shipments in shipmentsgroups.keys():
            if len(shipments) > 1:
                count = count+1
                if count > 1:
                    return True
        return False
