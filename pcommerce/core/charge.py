from persistent import Persistent

from zope.interface import implements

from pcommerce.core.interfaces import IChargeData

class ChargeData(Persistent):
    """ Base implementation of a charge data object
    """
    implements(IChargeData)
    
    title = u''
    price = 0.0
    
    def __init__(self, title, price):
        self.title = title
        self.price = price