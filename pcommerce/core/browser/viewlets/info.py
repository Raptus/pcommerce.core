from zope.component import getMultiAdapter

from plone.memoize.instance import memoize
from plone.app.layout.viewlets.common import ViewletBase

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class InfoViewlet(ViewletBase):
    index = ViewPageTemplateFile('info.pt')
    
    def update(self):
        self.product_view = getMultiAdapter((self.context, self.request), name=u'view')
    
    @property
    @memoize
    def product(self):
        return self.product_view.product
    
    @property
    @memoize
    def image(self):
        return self.product_view.image
    
    @property
    @memoize
    def images(self):
        return self.product_view.images
    
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
    def offer(self):
        return self.product_view.offer
    
    @property
    @memoize
    def variations(self):
        return self.product_view.variations