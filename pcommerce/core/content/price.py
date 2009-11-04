"""Price content type
"""

from AccessControl import ClassSecurityInfo

from zope.interface import implements

from Products.Archetypes.public import *

from pcommerce.core.interfaces import IPrice
from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.config import PROJECTNAME

PriceSchema = BaseContent.schema.copy() + Schema((

    FixedPointField(
        name='price',
        required=1,
        languageIndependent=True,
        widget=DecimalWidget(
            label=_(u'Price'),
        )
    ),

))

for field in ('description', 'creators','allowDiscussion','contributors','location','subject','language','rights','title',):
    if PriceSchema.has_key(field):
        PriceSchema[field].widget.visible = 0

PriceSchema['title'].required = False

class Price(BaseContent):
    """ A Price
    """
    implements(IPrice)

    portal_type = meta_type = "Price"
    schema = PriceSchema
    _at_rename_after_creation = False

registerType(Price, PROJECTNAME)