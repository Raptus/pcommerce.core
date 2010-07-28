"""Variation content-type
"""
from zope.interface import implements

try:
  from Products.LinguaPlone.public import *
except ImportError:
  # No multilingual support
  from Products.Archetypes.public import *
  
from Products.SingleKeywordWidget.widget import SingleKeywordWidget

from pcommerce.core.content.product import Product, ProductSchema

from pcommerce.core.interfaces import IVariation
from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.config import PROJECTNAME

VariationSchema = Schema((
    
    StringField(
        name='type',
        required=1,
        searchable=True,
        widget=SingleKeywordWidget(
            label=_(u'Type'),
            format='radio',
        )
    ),

    BooleanField(
        name='addPrice',
        languageIndependent=True,
        widget=BooleanWidget(
            label=_(u'Additional price'),
        )
    ),

)) + ProductSchema.copy()

VariationSchema['creators'].widget.visible = 0
VariationSchema.changeSchemataForField('no', 'overrides')
VariationSchema.changeSchemataForField('text', 'overrides')
VariationSchema.changeSchemataForField('relatedItems', 'overrides')
VariationSchema.moveField('title', before='type')
VariationSchema.moveField('addPrice', after='price')
VariationSchema.moveField('effectiveDate', after='imageCaption')
VariationSchema.moveField('expirationDate', after='effectiveDate')



VariationSchema['price'].widget.description = _(u'description_price', default=u'If multiple selected variations in different categories have unit prices, the greater price will be accounted for in pricing of the selected combination.')

class Variation(Product):
    """ A variation of a product
    """
    implements(IVariation)

    portal_type = meta_type = "Variation"
    schema = VariationSchema

registerType(Variation, PROJECTNAME)
