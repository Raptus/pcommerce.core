from zope.component import getMultiAdapter
from zope.interface import implements

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from plone.memoize.instance import memoize
from plone.app.content.browser.interfaces import IFolderContentsView
from plone.app.content.browser.foldercontents import FolderContentsTable

from pcommerce.core.currency import CurrencyAware
from pcommerce.core.interfaces import IPrice
from pcommerce.core.browser.product import Product

class Prices(Product, FolderContentsTable):
    """management view of all prices
    """
    implements(IFolderContentsView)

    template = ViewPageTemplateFile('prices.pt')
    
    def __call__(self):
        if self.request.get('prices', None):
            prices = self.context.objectIds()
            for price in self.request.get('prices', []):
                if not isinstance(price, str) and price.id in prices:
                    self.context[price.id].setPrice(price.price)
                    self.context[price.id].reindexObject()
        return self.template()
    
    @property
    @memoize
    def items(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        plone_view = getMultiAdapter((self.context, self.request), name=u'plone')
        utils = getToolByName(self.context, 'plone_utils')
        wftool = getToolByName(self.context, 'portal_workflow')
        results = catalog(object_provides=IPrice.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()), 'depth': 1})
        prices = []
        odd = True
        for price in results:
            prices.append({'uid': price.UID,
                           'id': price.getId,
                           'modified': plone_view.toLocalizedTime(price.ModificationDate, long_format=1),
                           'state_title': wftool.getTitleForStateOnType(price.review_state, price.portal_type),
                           'state_class': 'state-' + utils.normalizeString(price.review_state),
                           'is_expired': self.context.isExpired(price),
                           'title_or_id': price.pretty_title_or_id(),
                           'table_row_class': odd and 'odd' or 'even',
                           'raw_price': price.getPrice,
                           'price': CurrencyAware(price.getPrice),
                           'path': price.getPath,
                           'relative_url': price.getURL(relative=True),
                           'url': {'edit': '%s/edit' % price.getURL(),
                                   'sharing': '%s/@@sharing' % price.getURL()}})
            odd = not odd
        return prices
