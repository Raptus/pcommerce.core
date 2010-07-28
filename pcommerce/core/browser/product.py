from Acquisition import aq_inner, aq_parent

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from plone.memoize.instance import memoize

from pcommerce.core.interfaces import IVariation, IPrice, IPricing, IImaging, ITaxes
from pcommerce.core.currency import CurrencyAware

class Product(BrowserView):
    """view of a product
    """

    template = ViewPageTemplateFile('product.pt')

    def __call__(self):
        return self.template()
    
    @memoize
    def title(self):
        if IVariation.providedBy(self.context):
            return '%s (%s: %s)' % (self.product.Title().decode('utf-8'), self.context.getType().decode('utf-8'), self.context.Title().decode('utf-8'))
        return self.context.Title()
    
    @property
    @memoize
    def description(self):
        return self.context.Description() or self.product.Description()
    
    @property
    @memoize
    def text(self):
        return self.context.getText() or self.product.getText()
    
    @property
    @memoize
    def image(self):
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        width = int(props.getProperty('thumb_width_detail', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        context = None
        if self.context.getImage():
            context = self.context
        elif self.product.getImage():
            context = self.product
        if context is None:
            return None
        return {'caption': context.getImageCaption(),
                'thumb': '%s/%s' % (context.absolute_url(), width),
                'url': '%s/image_preview' % context.absolute_url()}
    
    @property
    @memoize
    def images(self):
        images = []
        odd = False
        i = 0
                      
        context = None
        
        if self.context.getImage():
            """ the variation have a image
            """
            image = self.image
            if image:
                image['parity'] = 'odd'            
                images.append(image)
                odd = True
                i = 1
            context = self.context
        elif not IImaging(self.context).getImages():
            """ the variation have not a image and not images in the content
            """
            image = self.image
            if image:
                image['parity'] = 'odd'            
                images.append(image)
                odd = True
                i = 1
            context = self.product
        else:
            """ the variation have not a image but a images in the content
            """
            context = self.context
                
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        width = int(props.getProperty('thumb_width_detail', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        
        for image_raw in IImaging(context).getImages():
            image = {'url': '%s/image_preview' % (image_raw.getURL()),
                     'thumb': '%s/%s' % (image_raw.getURL(), width),
                     'caption': image_raw.Title
                    }
            odd = not odd
            if odd:
                image['parity'] = 'odd'
            else:
                image['parity'] = 'even'
            images.append(image)
            i += 1
          
        return images
          
    @property
    @memoize
    def product(self):
        context = aq_inner(self.context)
        if IVariation.providedBy(context):
            return aq_parent(context)
        return self.context
    
    @property
    def price(self):
        if IVariation.providedBy(self.context):
            return CurrencyAware(IPricing(self.product).getPrice([aq_inner(self.context),]))
        return CurrencyAware(IPricing(self.product).getPrice())
    
    @property
    def base_price(self):
        if IVariation.providedBy(self.context):
            return CurrencyAware(IPricing(self.product).getBasePrice([aq_inner(self.context),]))
        return CurrencyAware(IPricing(self.product).getBasePrice())
    
    @property
    @memoize
    def offer(self):
        return self.price.getValue() < self.base_price.getValue()
    
    @property
    def variations(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        results = catalog(object_provides=IVariation.__identifier__, path={'query': '/'.join(self.product.getPhysicalPath())})
        variations = {}
        for variation in results:
            if not variations.has_key(variation.getType):
                variations[variation.getType] = []
            if not variation.getAddPrice:
                price_adapter = IPricing(variation.getObject())
            variations[variation.getType].append({
                'uid': variation.UID,
                'name': variation.Title,
                'price': CurrencyAware(IPricing(self.product).getPrice([variation.getObject()])),
                'price_raw': IPricing(self.product).getPrice([variation.getObject()]),
                'base_price': CurrencyAware(variation.getAddPrice and self.base_price.getValue() + float(variation.getPrice) or price_adapter.getBasePrice()),
                'base_price_raw':variation.getAddPrice and self.base_price.getValue() + float(variation.getPrice) or price_adapter.getBasePrice(),
                'add_price': variation.getAddPrice and CurrencyAware(float(variation.getPrice)) or None,
                'add_price_raw': variation.getAddPrice and float(variation.getPrice) or None, })


        return [{'name': type[0],
                 'variations': type[1]} for type in variations.items()]
