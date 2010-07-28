from zope.component import getMultiAdapter
import random

from plone.memoize.instance import memoize
from plone.app.layout.viewlets.common import ViewletBase

from Products.CMFCore.utils import getToolByName

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.interfaces import IPricing, IProduct
from pcommerce.core.currency import CurrencyAware

class HotViewlet(ViewletBase):
    index = ViewPageTemplateFile('hot.pt')
        
    def products(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        columns = int(props.getProperty('hot_columns', 3))
        no = int(props.getProperty('no_hot_products', 6))
        width = int(props.getProperty('thumb_width_hot_products', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        results = list(catalog(object_provides=IProduct.__identifier__, hot=True))
        if not results:
            return None
        items = []
        i = 0
        while len(items) < no and len(results):
            item = results.pop(random.randrange(len(results)))
            object = item.getObject()
            col = i % columns + 1
            i += 1
            adapter = IPricing(object)
            image = None
            if object.getImage():
                image = {'caption': object.getImageCaption(),
                         'thumb': '%s/%s' % (item.getURL(), width)}
            item = {'uid': item.UID,
                    'class': 'col%s' % col,
                    'title': item.Title,
                    'description': item.Description,
                    'price': CurrencyAware(adapter.getPrice()),
                    'base_price': CurrencyAware(adapter.getBasePrice()),
                    'offer': adapter.getPrice() < adapter.getBasePrice(),
                    'image': image,
                    'url': item.getURL()}
            items.append(item)
        return items