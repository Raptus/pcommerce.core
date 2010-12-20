"""Product content-type
"""

from AccessControl import ClassSecurityInfo

from zope.interface import implements

try:
  from Products.LinguaPlone.public import *
except ImportError:
  # No multilingual support
  from Products.Archetypes.public import *

from Products.validation import V_REQUIRED

from Products.CMFCore.permissions import View

from Products.ATContentTypes.content.document import ATDocumentBase, ATDocumentSchema

from pcommerce.core.interfaces import IProduct
from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.config import PROJECTNAME

from Products.CMFPlone.interfaces import INonStructuralFolder
from Products.CMFPlone import PloneMessageFactory as _p

from zope.schema.interfaces import IVocabularyFactory

ProductSchema = ATDocumentSchema.copy() + Schema((

    StringField(
        name='no',
        searchable=1,
        widget=StringWidget(
            label=_('No'),
        )
    ),

    FixedPointField(
        name='price',
        languageIndependent=True,
        widget=DecimalWidget(
            label=_(u'Price'),
        )
    ),

    BooleanField(
        name='new',
        languageIndependent=True,
        widget=BooleanWidget(
            label=_(u'New product'),
        )
    ),

    BooleanField(
        name='hot',
        languageIndependent=True,
        widget=BooleanWidget(
            label=_(u'Hot product'),
        )
    ),
    
    LinesField(
        name='shipments',
        required = True,
        multiValued = True,
        widget = MultiSelectionWidget(label = _(u'label_shipment_methods', default=u'Shipment methods'),
                                      description = _(u'description_shipment_methods', default=u'Shipment methods for this product'),
                                      format = 'checkbox',
                                     ),
        vocabulary_factory = u"pcommerce.core.vocabulary.shipments"
    ),

    ImageField(
        name='image',
        languageIndependent=True,
        swallowResizeExceptions=True,
        max_size='no',
        sizes={'large'   : (768, 768),
               'preview' : (400, 400),
               'mini'    : (200, 200),
               'thumb'   : (128, 128),
               'tile'    :  (64, 64),
               'icon'    :  (32, 32),
               'listing' :  (16, 16),
               },
        validators=(('isNonEmptyFile', V_REQUIRED),
                    ('checkImageMaxSize', V_REQUIRED),),
        widget=ImageWidget(label= _p(u'label_news_image', default=u'Image'),
                           show_content_type = False,),
    ),

    StringField(
        name='imageCaption',
        required = False,
        searchable = True,
        widget = StringWidget(description = '',
                              label = _p(u'label_image_caption', default=u'Image Caption'),
                              size = 40)
    ),
        
))

for field in ('creators','contributors','location','subject','language','rights','presentation', 'tableContents',):
    if ProductSchema.has_key(field):
        ProductSchema[field].widget.visible = 0

ProductSchema['excludeFromNav'].default = 1
ProductSchema.changeSchemataForField('relatedItems', 'default')
ProductSchema.moveField('no', after='title')
ProductSchema.moveField('price', after='no')
ProductSchema.moveField('hot', after='description')
ProductSchema.moveField('new', after='hot')
ProductSchema.moveField('shipments', after='new')
ProductSchema.moveField('image', after='shipments')
ProductSchema.moveField('imageCaption', after='image')

class Product(OrderedBaseFolder, ATDocumentBase):
    """ A product
    """
    implements(IProduct, INonStructuralFolder)

    portal_type = meta_type = "Product"
    schema = ProductSchema
    security = ClassSecurityInfo()
    _at_rename_after_creation = True

    security.declareProtected(View, 'tag')
    def tag(self, **kwargs):
        """Generate image tag using the api of the ImageField
        """
        if 'title' not in kwargs:
            kwargs['title'] = self.getImageCaption()
        return self.getField('image').tag(self, **kwargs)

registerType(Product, PROJECTNAME)