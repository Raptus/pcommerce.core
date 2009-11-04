from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.memoize.instance import memoize

from Products.CMFCore.utils import getToolByName

from pcommerce.core.currency import CurrencyAware
from pcommerce.core.config import CheckOut
from pcommerce.core.interfaces import IShoppingCart

class ShoppingCartView(BrowserView):
    """view of the shopping cart
    """

    template = ViewPageTemplateFile('templates/cart.pt')

    def __call__(self):
        self.request.set('disable_border', 1)
        self.cart = IShoppingCart(self.context)
        return self.template()
    
    @property
    @memoize
    def size(self):
        return self.cart.amount()
    
    @property
    @memoize
    def products(self):
        return self.cart.getProducts()
    
    @property
    @memoize
    def checkout(self):
        return getToolByName(self.context, 'portal_membership').checkPermission(CheckOut, self.context)
    
    @property
    @memoize
    def price(self):
        return CurrencyAware(self.cart.getPrice())