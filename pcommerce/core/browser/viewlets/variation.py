from zope.component import getMultiAdapter

from plone.memoize.instance import memoize
from plone.app.layout.viewlets.common import ViewletBase

from Products.CMFCore.utils import getToolByName

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from pcommerce.core.interfaces import IPricing, IProduct, IVariation
from pcommerce.core.currency import CurrencyAware

class VariationViewlet(ViewletBase):
    index = ViewPageTemplateFile('templates/variation.pt')
    
    @property
    @memoize
    def product(self):
        return self.view.product
    
    def variation_items(self):
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        columns = int(props.getProperty('columns', 3))
        width = int(props.getProperty('thumb_width', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        items = []
        i = 0
              
        catalog = getToolByName(self.product, 'portal_catalog')
        variations = catalog(object_provides=IVariation.__identifier__, path={'query': '/'.join(self.product.getPhysicalPath())})
        
        for variation in variations:
            col = i % columns + 1
            i += 1
            
            variation = variation.getObject()
            adapter = IPricing(variation)
            
            if variation.UID() != self.context.UID():
                image = None
                if variation.getImage():
                    image = {'caption': variation.getImageCaption(),
                             'thumb': '%s/%s' % (variation.absolute_url(), width)}
                
                items.append({'uid': variation.UID(),
                              'class': 'col%s' % col,
                              'title': '%s: %s' % (variation.getType(), variation.Title()),
                              'description': variation.Description() or self.product.Description(),
                              'price': CurrencyAware(adapter.getPrice()),
                              'base_price': CurrencyAware(adapter.getBasePrice()),
                              'offer': adapter.getPrice() < adapter.getBasePrice(),
                              'image': image,
                              'url': variation.absolute_url()})
        return items