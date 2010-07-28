from zope.interface import implements, Interface
from zope.component import adapts, getAdapters

from pcommerce.core import interfaces

class Shipment(object):
    """shipment-registry"""
    implements(interfaces.IShipmentRegistry)
    adapts(Interface)
    
    def __init__(self, context):
        self.context = context

    def getShipmentMethods(self):
        """get all registered shipment-methods"""
        return dict([(name, adapter) for name, adapter in getAdapters((self.context,), interfaces.IShipmentMethod)])

class Payment(object):
    """payment-registry"""
    implements(interfaces.IPaymentRegistry)
    adapts(Interface)
    
    def __init__(self, context):
        self.context = context

    def getPaymentMethods(self):
        """get all registered payment-methods"""
        return dict([(name, adapter) for name, adapter in getAdapters((self.context,), interfaces.IPaymentMethod)])
