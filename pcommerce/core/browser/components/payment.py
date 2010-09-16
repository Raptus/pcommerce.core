from zope.component import queryMultiAdapter

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.interfaces import IPaymentView
from pcommerce.core.browser.components.base import BaseComponent

class PaymentComponent(BaseComponent):
    index = ViewPageTemplateFile('payment.pt')
    
    dependencies = ('payments',)

    def validate(self):
        return self.paymentview and self.paymentview.validate()
    
    def process(self):
        if self.paymentview:
            self.order.paymentdata = self.paymentview.process()
        
    def renders(self):
        if self.paymentview and self.paymentview.renders():
            return True
        if len(self._payments()) == 1:
            paymentview = queryMultiAdapter((self._payments().values()[0], self.request), name=self.__name__, interface=IPaymentView)
            if paymentview is not None:
                return paymentview.__of__(self.context).renders()
        return False