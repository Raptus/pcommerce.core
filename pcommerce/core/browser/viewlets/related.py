from zope.component import getMultiAdapter

from plone.memoize.instance import memoize
from plone.app.layout.viewlets.common import ViewletBase

from Products.CMFCore.utils import getToolByName

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.interfaces import IPricing, IProduct
from pcommerce.core.currency import CurrencyAware

class RelatedViewlet(ViewletBase):
    index = ViewPageTemplateFile('related.pt')
    
    def update(self):
        self.view = getMultiAdapter((self.context, self.request), name=u'view')
    
    @property
    @memoize
    def product(self):
        return self.view.product
        
    @property
    @memoize
    def related_items(self):
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        columns = int(props.getProperty('columns', 3))
        width = int(props.getProperty('thumb_width', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        items = []
        i = 0
        for item in self.product.getRelatedItems():
            if IProduct.providedBy(item):
                col = i % columns + 1
                i += 1
                adapter = IPricing(item)
                image = None
                if item.getImage():
                    image = {'caption': item.getImageCaption(),
                             'thumb': '%s/%s' % (item.absolute_url(), width)}
                items.append({'uid': item.UID(),
                              'class': 'col%s' % col,
                              'title': item.Title(),
                              'description': item.Description(),
                              'price': CurrencyAware(adapter.getPrice()),
                              'base_price': CurrencyAware(adapter.getBasePrice()),
                              'offer': adapter.getPrice() < adapter.getBasePrice(),
                              'image': image,
                              'url': item.absolute_url()})
        return items