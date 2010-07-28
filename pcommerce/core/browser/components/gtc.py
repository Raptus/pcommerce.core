from zope.component import getMultiAdapter
from plone.memoize.instance import memoize

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from pcommerce.core.browser.components.base import BaseComponent
from pcommerce.core import PCommerceMessageFactory as _
        
class GTCComponent(BaseComponent):
    template = ViewPageTemplateFile('gtc.pt')
    
    def validate(self):
        self.errors = {}
        if self.request.form.get('gtc'):
            return True
        self.errors['gtc'] = _('The general terms and conditions have to be accepted to finish your check out.')
        return False
    
    def process(self):
        return
        
    @memoize
    def gtc(self):
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        return '%s/%s' % (portal_state.portal_url(), props.getProperty('gtc', ''))
