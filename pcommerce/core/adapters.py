from Acquisition import aq_parent

from zope.interface import implements, Interface
from zope.component import adapts, getMultiAdapter
from zope.annotation.interfaces import IAnnotations

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface.image import IImageContent

from pcommerce.core import interfaces

ANNOTATIONS_KEY_TAXES = 'pcommerce.core.taxes'
ANNOTATIONS_KEY_TAX_INCLUDED = 'pcommerce.core.tax_included'

class Imaging(object):
    """ An adapter to handle the images of a product
    """ 
    implements(interfaces.IImaging)
    adapts(interfaces.IProduct)
    
    def __init__(self, context):
        self.context = context
    
    def getImages(self):
        """ All image inside of the product
        """
        catalog = getToolByName(self.context, 'portal_catalog')
        images = catalog(object_provides=IImageContent.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()),
                                                                             'depth': 1})
        return images
        
class Pricing(object):
    """ An adapter to handle prices of a product
    """
    implements(interfaces.IPricing)
    adapts(interfaces.IProduct)
    
    def __init__(self, context):
        self.context = context
    
    def getPrice(self, variations=[]):
        """ The product price in combination of variations 
        """
        price = 0
        if self.context.getPrice() is not None:
            price = float(self.context.getPrice())
        catalog = getToolByName(self.context, 'portal_catalog')
        prices = [float(p.getPrice or 0) for p in catalog(object_provides=interfaces.IPrice.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()),'depth': 1})]
        prices.append(price)
        if len(prices)>0:
            price = min(prices)
        add = 0
        prices = []
        if len(variations):
            for variation in variations:
                if variation.getAddPrice():
                    add += float(variation.getPrice())
                else:
                    v_prices = [float(v.getPrice or 0) for v in catalog(object_provides=interfaces.IPrice.__identifier__, path={'query': '/'.join(variation.getPhysicalPath()),'depth': 1})]
                    if variation.getPrice() is not None:
                        v_prices.append(float(variation.getPrice()))
                    if len(v_prices)>0:
                        prices.append(min(v_prices))
                        
        if len(prices)>0 and float(price) < float(max(prices)):
            price = max(prices)
        return float(price) + float(add)
    
    def getBasePrice(self, variations=[]):
        """ The base price defined on the product
        """
        return float(self.context.getPrice() or 0)
        
class Taxes(object):
    """ An adapter to handle taxes based on zones
        
        len(Taxes)
        Taxes.has_key(key)
        Taxes.items()
        Taxes[key]
        Taxes[key] = value
        del(Taxes[key])
    """
    implements(interfaces.ITaxes)
    adapts(Interface)
    
    _items = {}
    _taxincl = None
    
    def __init__(self, context):
        self.context = context
        self.portal = getMultiAdapter((self.context, self.context.REQUEST), name=u'plone_portal_state').portal()
        annotations = IAnnotations(self.portal)
        self._items = dict(annotations.get(ANNOTATIONS_KEY_TAXES, ()))
        self._taxincl = annotations.get(ANNOTATIONS_KEY_TAX_INCLUDED, None)
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, key):
        return self._items[key]
    
    def __setitem__(self, key, value):
        if not isinstance(value[0], float):
            raise AttributeError, 'value has to be a float got %s' % type(value[0])
        self._items[key] = value
        self._save()
    
    def __delitem__(self, key):
        del(self._items[key])
        self._save()
    
    def has_key(self, key):
        return self._items.has_key(key)
    
    def items(self):
        return self._items.items()
    
    def keys(self):
        return self._items.keys()
    
    def get_taxincl(self):
        return self._taxincl
    
    def set_taxincl(self, value):
        self._taxincl = value
        annotations = IAnnotations(self.portal)
        annotations[ANNOTATIONS_KEY_TAX_INCLUDED] = self._taxincl
        
    def del_taxincl(self):
        del self._taxincl
        annotations = IAnnotations(self.portal)
        annotations[ANNOTATIONS_KEY_TAX_INCLUDED] = None
        
    taxincl = property(get_taxincl, set_taxincl, del_taxincl, "I'm the 'tax_incl' property.")

    
    def edit(self, taxes):
        """ edits the taxes
        
            taxes has to be a list of dicts with keys 'zone', 'tax' and 'taxname'
        """
        self._items = {}
        self._save()
        for tax in taxes:
            self[tax['zone']] = (tax['tax'], tax['taxname'])
    
    def _save(self):
        annotations = IAnnotations(self.portal)
        annotations[ANNOTATIONS_KEY_TAXES] = self.items()
