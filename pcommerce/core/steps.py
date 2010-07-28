from zope.interface import implementer, Interface
from zope.component import adapter

from pcommerce.core.interfaces import ISteps
from pcommerce.core import PCommerceMessageFactory as _

@adapter(Interface)
@implementer(ISteps)
def steps(context):
    return ({'name':_('Address'), 'components':('address',)},
            {'name':_('Shipment'), 'components':('shipments',)},
            {'name':_('Shipment'), 'components':('shipment',)},
            {'name':_('Payment'), 'components':('payments',)},
            {'name':_('Payment'), 'components':('payment',)},
            {'name':_('Overview'), 'components':('overview', 'gtc',)},
            {'name':_('Confirmation'), 'components':('confirmation',)})