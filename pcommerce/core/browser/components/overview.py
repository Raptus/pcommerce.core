from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.browser.components.base import BaseComponent
        
class OverviewComponent(BaseComponent):
    template = ViewPageTemplateFile('overview.pt')
    
    def validate(self):
        return True
    
    def process(self):
        return
        
    @property
    def address(self):
        return self.order.address
