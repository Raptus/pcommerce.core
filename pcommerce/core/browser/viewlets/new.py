import random
from zope.component import getMultiAdapter

from plone.memoize.instance import memoize
from plone.app.layout.viewlets.common import ViewletBase

from Products.CMFCore.utils import getToolByName

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.interfaces import IPricing, IProduct
from pcommerce.core.currency import CurrencyAware

class NewViewlet(ViewletBase):
    index = ViewPageTemplateFile('templates/new.pt')
        
    def products(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        columns = int(props.getProperty('new_columns', 2))
        no = int(props.getProperty('no_new_products', 2))
        width = int(props.getProperty('thumb_width_new_products', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        results = list(catalog(object_provides=IProduct.__identifier__, new=True))
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