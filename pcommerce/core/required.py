from zope.interface import implementer, Interface
from zope.component import adapter

from pcommerce.core.interfaces import IRequiredComponents

@adapter(Interface)
@implementer(IRequiredComponents)
def components(context):
    return ('address', 'shipments', 'shipment', 'payments', 'payment', 'overview', 'gtc',)
