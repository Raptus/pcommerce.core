from zope.interface import implements, Interface
from zope.component import adapts, getAdapter
from zope.event import notify

from pcommerce.core import interfaces
from pcommerce.core.config import FAILED, PROCESSED, SENT
from pcommerce.core.events import OrderProcessedEvent, OrderProcessingFailedEvent

class PaymentProcessor(object):
    """"""
    implements(interfaces.IPaymentProcessor)
    adapts(Interface)

    def __init__(self, context):
        self.context = context
        
    def processOrder(self, orderid, paymentid, lang=None):
        orderid = int(orderid)
        registry = interfaces.IOrderRegistry(self.context)
        order = registry.getOrder(orderid)
        if not order or not order.paymentid == paymentid:
            return 'no matching order found'
        if order.state is not PROCESSED:
            if order.state < SENT:
                registry.send(orderid, lang)
            method = getAdapter(self.context, name=paymentid, interface=interfaces.IPaymentMethod)
            if method.verifyPayment(order):
                order.state = PROCESSED
                notify(OrderProcessedEvent(order))
                return 'payment successfully processed'
            else:
                order.state = FAILED
                notify(OrderProcessingFailedEvent(order))
                return 'processing payment failed'
        return 'payment already processed'