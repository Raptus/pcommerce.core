from plone.app.layout.viewlets.common import ViewletBase

from Products.CMFCore.utils import getToolByName

from Products.statusmessages.interfaces import IStatusMessage

from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.interfaces import IShoppingCart

class ProcessorViewlet(ViewletBase):
    
    def update(self):
        self.statusmessages = IStatusMessage(self.request)
        try:
            amount = int(self.request.get('cartAmount', 1))
        except:
            self.statusmessages.addStatusMessage(_(u'Please specify an amount'), 'error')
            return
        
        self.added = self.removed = 0
        adapter = IShoppingCart(self.context)
        
        if self.request.get('cartAdd', None):
            self.added += adapter.add(self.request.get('cartAdd', None), amount)
        
        elif self.request.get('cartVariation', None):
            self.added += adapter.addVariation(self.request.get('cartVariation', None), amount)
            if not self.added:
                self.statusmessages.addStatusMessage(_(u'Please select a variation'), 'error')
        
        elif self.request.get('cartRemove', None):
            self.removed -= adapter.remove(self.request.get('cartRemove', None), self.request.get('cartRemoveAmount', None))
        
        elif self.request.get('cartEdit', None):
            a, r = adapter.edit(self.request.get('cartEdit', None))
            self.added += a
            self.removed += r
            
        self.addStatusMessages()
        
    def index(self):
        return ''
        
    def addStatusMessages(self):
        if self.added > 1:
            self.statusmessages.addStatusMessage(_(u'Added ${count} items to cart', mapping={'count': self.added}), 'info')
        elif self.added == 1:
            self.statusmessages.addStatusMessage(_(u'Added item to cart'), 'info')
        if self.removed > 1:
            self.statusmessages.addStatusMessage(_(u'Removed ${count} items from cart', mapping={'count': self.removed}), 'info')
        elif self.removed == 1:
            self.statusmessages.addStatusMessage(_(u'Removed item from cart'), 'info')
