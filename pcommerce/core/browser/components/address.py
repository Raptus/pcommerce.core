from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as _p

from pcommerce.core.browser.components.base import BaseComponent
from pcommerce.core import interfaces

class AddressComponent(BaseComponent):
    template = ViewPageTemplateFile('address.pt')
    
    def validate(self):
        self.errors = {}
        factory = interfaces.IAddressFactory(self.request)
        self.errors = factory.validate('customer')
        return len(self.errors) == 0
    
    def process(self):
        factory = interfaces.IAddressFactory(self.request)
        self.order.address = factory.create('customer')
        taxes = interfaces.ITaxes(self.context)
        if self.order.address.zone and taxes.has_key(self.order.address.zone):
            self.order.zone = (self.order.address.zone, taxes[self.order.address.zone])
    
    @property
    def address(self):
        return self.order.address
        