from persistent import Persistent

from zope.interface import implements

from pcommerce.core.interfaces import IPaymentData, IShipmentData

class BaseData(Persistent):
    pretaxcharge = 0.0
    posttaxcharge = 0.0
            
    def __init__(self, shipmentid, pretaxcharge=0.0, posttaxcharge=0.0, **kwargs):
        self.shipmentid = shipmentid
        self.pretaxcharge = pretaxcharge
        self.posttaxcharge = posttaxcharge
        for key, value in kwargs.items():
            setattr(self, key, value)

class PaymentData(BaseData):
    implements(IPaymentData)
    
class ShipmentData(BaseData):
    implements(IShipmentData)
    
