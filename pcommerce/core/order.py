from zope.interface import implements

from pcommerce.core.config import INITIALIZED
from pcommerce.core.interfaces import IOrder

class Order(object):
    """"""
    implements(IOrder)
    
    state = INITIALIZED
    orderid = ''
    userid = ''
    products = []
    date = None
    price = 0.0
    currency = ''
    zone = None
    delivery = None
    
    def __init__(self,
                 orderid,
                 userid,
                 price=0.0,
                 currency='',
                 date=None,
                 zone=None,
                 products=[],
                 delivery=None):
        """"""
        self.orderid = orderid
        self.userid = userid
        self.price = price
        self.currency = currency
        self.date = date
        self.zone = zone
        self.products = products
        self.delivery = delivery
        
    @property
    def tax(self):
        return self.zone[1]
    
    @property
    def price_tax(self):
        return self.price * self.tax / 100
    
    @property
    def total(self):
        return self.price + self.price_tax