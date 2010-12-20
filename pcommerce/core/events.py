from zope.interface import implements

from pcommerce.core import interfaces

class OrderEvent(object):
    
    def __init__(self, registry, order):
        self.registry = registry
        self.order = order
        
class OrderProcessingSuccessfulEvent(OrderEvent):
    implements(interfaces.IOrderProcessingSuccessfulEvent)
    
class OrderProcessingFailedEvent(OrderEvent):
    implements(interfaces.IOrderProcessingFailedEvent)
        
class OrderProcessedEvent(OrderEvent):
    implements(interfaces.IOrderProcessedEvent)

class OrderCreatedEvent(OrderEvent):
    implements(interfaces.IOrderCreatedEvent)

class OrderAboutToBeRecreatedEvent(OrderEvent):
    implements(interfaces.IOrderAboutToBeRecreatedEvent)

class OrderRecreatedEvent(OrderEvent):
    implements(interfaces.IOrderRecreatedEvent)

class OrderRecoveredEvent(OrderEvent):
    implements(interfaces.IOrderRecoveredEvent)

class OrderSentEvent(OrderEvent):
    implements(interfaces.IOrderSentEvent)

class OrderFailedEvent(OrderEvent):
    implements(interfaces.IOrderFailedEvent)

class OrderCanceledEvent(OrderEvent):
    implements(interfaces.IOrderCanceledEvent)
