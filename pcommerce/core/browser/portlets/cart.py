from zope.interface import implements
from zope.component import getMultiAdapter

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from Products.CMFCore.utils import getToolByName

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.currency import CurrencyAware
from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.config import CheckOut
from pcommerce.core.interfaces import IShoppingCart

class IShoppingCartPortlet(IPortletDataProvider):
    """A portlet which renders a users shopping cart
    """

class Assignment(base.Assignment):
    implements(IShoppingCartPortlet)

    title = _(u'Shopping cart')

class Renderer(base.Renderer):

    def update(self):
        self.cart = IShoppingCart(self.context)

    @property
    def portal_url(self):
        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        return portal_state.portal_url()
    
    @property
    def size(self):
        return self.cart.amount()
    
    @property
    def price(self):
        return CurrencyAware(self.cart.getPrice())
    
    @property
    def checkout(self):
        return getToolByName(self.context, 'portal_membership').checkPermission(CheckOut, self.context)

    render = ViewPageTemplateFile('cart.pt')

class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()
