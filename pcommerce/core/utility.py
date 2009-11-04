from zope.interface import implements
from zope.component import getUtilitiesFor

from pcommerce.core.interfaces import IPaymentRegistry, IPaymentMethod

class PaymentRegistryUtility(object):
    """payment-registry"""
    implements(IPaymentRegistry)

    payments = []

    def getPaymentMethods(self):
        """get all registered payment-methods"""
        return dict([(name, utility) for name, utility in getUtilitiesFor(IPaymentMethod)])

registry = PaymentRegistryUtility()