from Acquisition import aq_parent, aq_inner

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from pcommerce.core.interfaces import IPricing, IProduct, IVariation
from pcommerce.core.currency import CurrencyAware

class GetPrcie(BrowserView):
    """ A AJAX interface for getPrece of the product
    """

    template = ViewPageTemplateFile('getprice.pt')

    def __call__(self):
        return self.template()
    
    def price(self):
        import logging
        v_uid = None
        product = aq_inner(self.context)
        if IVariation.providedBy(product):
            product = aq_parent(product)
            v_uid = self.context.UID()
        
        v_uids = self.request.get('v', '')
        v_uids = v_uids.split(',')
        v_uids = [uid for uid in v_uids if uid != '']
        if not len(v_uids) and v_uid is not None:
            v_uids = [v_uid,]
        
        catalog = getToolByName(self.context, 'uid_catalog')
        variations = catalog(object_provides=IVariation.__identifier__, UID=v_uids)
        variations = [variation.getObject() for variation in variations]
        
        price = IPricing(product).getPrice(variations)

        return CurrencyAware(price)