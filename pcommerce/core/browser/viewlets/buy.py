from zope.component import getMultiAdapter

from plone.memoize.instance import memoize
from plone.app.layout.viewlets.common import ViewletBase

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class BuyViewlet(ViewletBase):
    index = ViewPageTemplateFile('buy.pt')
    
    def update(self):
        ViewletBase.update(self)
        self.product_view = getMultiAdapter((self.context, self.request), name=u'view')
    
    @property
    @memoize
    def product(self):
        return self.product_view.product
    
    @property
    @memoize
    def price(self):
        return self.product_view.price
    
    @property
    @memoize
    def base_price(self):
        return self.product_view.base_price
    
    @property
    @memoize
    def variations(self):
        types = []
        for type in self.product_view.variations:
            variations = []
            for variation in type['variations']:
                if self.context.Title() == variation['name']:
                    variation['selected'] = True
                else:
                    variation['selected'] = False
                variations.append(variation)
            type['variations'] = variations
            types.append(type)
        return types
    
    