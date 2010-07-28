from zope.interface import implementer, implements
from zope.component import adapter, adapts
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from Products.Archetypes.interfaces import IFieldDefaultProvider

from pcommerce.core.interfaces import IShipmentRegistry, IProduct

@implementer(IVocabularyFactory)
def shipments(context):
    shipments = []
    registry = IShipmentRegistry(context)
    r_shipments = registry.getShipmentMethods()
    for name, shipment in r_shipments.items():
        shipments.append(SimpleTerm(name, name, shipment.title))
    return SimpleVocabulary(shipments)

class ShipmentsDefault(object):
    implements(IFieldDefaultProvider)
    adapts(IProduct)
    def __init__(self, context):
        self.context = context
    def __call__(self):
        vocabulary = shipments(self.context)
        for term in vocabulary:
            yield term.value
