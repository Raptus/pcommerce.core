from persistent.mapping import PersistentMapping

from zope.component import queryMultiAdapter

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.interfaces import IShipmentView
from pcommerce.core.browser.components.base import BaseComponent

class ShipmentComponent(BaseComponent):
    template = ViewPageTemplateFile('shipment.pt')
    
    dependencies = ('shipments',)
    
    def validate(self):
        valid = True
        for shipment in self.shipments:
            if shipment['view'] is not None:
                if not shipment['view'].validate():
                    valid = False
        return valid
    
    def process(self):
        self.order.shipmentdata = PersistentMapping()
        for shipment in self.shipments:
            if shipment['view'] is not None:
                shipmentdata = shipment['view'].process()
                self.order.shipmentdata[shipmentdata.id] = shipmentdata
                
    def renders(self):
        for shipment in self.shipments:
            if shipment['renders']:
                return True
        for shipmentids in self._shipmentgroups().keys():
            if not len(shipmentids) == 1:
                continue
            shipmentview = queryMultiAdapter((self._shipments()[shipmentids[0]], self.request), name=self.__name__, interface=IShipmentView)
            if shipmentview is not None:
                if shipmentview.__of__(self.context).renders():
                    return True
        return False
    
    @property
    def multiple(self):
        count = 0
        for shipment in self.shipments:
            if shipment['renders']:
                count += 1
        return count > 1
