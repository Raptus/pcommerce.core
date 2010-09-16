from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.browser.components.base import BaseComponent
from pcommerce.core import PCommerceMessageFactory as _

class PaymentsComponent(BaseComponent):
    index = ViewPageTemplateFile('payments.pt')
    error = None
    
    def validate(self):
        self.error = None
        if len(self._payments()) == 1:
            return True
        id = self.request.form.get('payment_id')
        if id is not None and self._payments().has_key(id):
            return True
        self.error = _(u'Please select a payment method.')
        return False
    
    def process(self):
        id = self.request.form.get('payment_id', len(self._payments()) == 1 and self.payments[0]['id'])
        self.order.paymentid = id
        if self.order.paymentdata and not self.order.paymentdata.id == id:
            self.order.paymentdata = None
    
    def renders(self):
        if len(self._payments())>1:
            return True
        return False
