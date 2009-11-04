from zope.interface import implements

from interfaces import IOrderProcessedEvent, IOrderProcessingFailedEvent

class OrderEvent(object):
    
    def __init__(self, order):
        self.order = order
        
class OrderProcessedEvent(OrderEvent):
    implements(IOrderProcessedEvent)
    
class OrderProcessingFailedEvent(OrderEvent):
    implements(IOrderProcessingFailedEvent)