from Acquisition import aq_inner, aq_parent

from zope.interface import implements

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface.image import IImageContent

from plone.memoize.instance import memoize
from plone.app.content import browser
from plone.app.content.batching import Batch

from pcommerce.core.interfaces import IPricing, IShopFolder, IShop, IProduct
from pcommerce.core.currency import CurrencyAware

batching_path = '/'.join(browser.__path__)

class ShopHome(BrowserView):
    """ shop home view
    """
    implements(IShop)
    
    template = ViewPageTemplateFile('folder.pt')

    def __call__(self):
        return self.template()

class ShopFolderListing(BrowserView):
    """ shop folder listing
    """
    implements(IShopFolder)

    template = ViewPageTemplateFile('folder.pt')
    batching = ViewPageTemplateFile('%s/batching.pt' % batching_path)

    def __call__(self):
        self.page = int(self.request.get('pagenumber', 1))
        self.url = self.context.absolute_url()
        return self.template()

    @property
    @memoize
    def batch(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        columns = int(props.getProperty('columns', 3))
        width = int(props.getProperty('thumb_width', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        results = catalog(object_provides=IProduct.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()), 'depth': 1}, sort_on='getObjPositionInParent')
        items = []
        i = 0
        start = (self.page-1) * (columns * 5)
        end = start + columns * 5
        for item in results:
            if start <= i < end:
                object = item.getObject()
                col = i % columns + 1
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
            else:
                item = {'uid': item.UID,
                        'title': item.Title,
                        'description': item.Description,
                        'url': item.getURL()}
            i += 1
            items.append(item)
        return Batch(items, columns * 5, self.page, 5)
        
    @property
    @memoize
    def multiple_pages(self):
        return self.batch.size > self.batch.pagesize
