from plone.memoize.instance import memoize

from Products.statusmessages.interfaces import IStatusMessage
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _p

from pcommerce.core.interfaces import ITaxes
from pcommerce.core import PCommerceMessageFactory as _

class PCommerceConfiglet(BrowserView):
    """PCommerce configlet
    """

    template = ViewPageTemplateFile('configlet.pt')
    properties = ('productname','gtc','post_checkout','email_address',)
    values = {}

    def __call__(self):
        self.request.set('disable_border', True)
        self.errors = {}
        
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        if self.request.form.has_key('pcommerce_save'):
            adapter = ITaxes(self.context)
            taxes = []
            raw = self.request.form.get('taxes', [])
            for tax in raw:
                if not tax.has_key('remove') or not tax['remove']:
                    try:
                        tax = {'id': tax['id'],
                               'tax': float(tax['tax']),
                               'zone': tax['zone'],
                               'taxname': tax['taxname']}
                        if tax['zone'] == '':
                            self.errors[tax['id']] = _(u'Please provide a zone name')
                        elif tax['taxname'] == '':
                            self.errors[tax['id']] = _(u'Please provide a tax name')
                        if not self.errors.has_key(tax['id']):
                            taxes.append(tax)
                    except:
                        self.errors[tax['id']] = _(u'Please enter a floating point number (e.g. 7.6)')
            for prop in self.properties:
                self.values[prop] = self.request.form.get(prop, '')
            
            
            taxincl = None
            tax = self.request.form.get('taxincl.tax', '')
            taxname = self.request.form.get('taxincl.taxname', '')
            
            try:                   
                if taxname == '' and tax != '':
                    self.errors['taxincl'] = _(u'Please provide a tax name')
                else:
                    if tax == '':
                      tax = 0.0
                    taxincl = (float(tax), taxname)
            except:
                self.errors['taxincl'] = _(u'Please enter a floating point number (e.g. 7.6)')
                
            if not self.errors:
                adapter.edit(taxes)
                adapter.taxincl = taxincl
                IStatusMessage(self.request).addStatusMessage(_p('Properties saved'), 'info')
                for prop in self.properties:
                    if prop == 'columns':
                        self.values[prop] = int(self.values[prop])
                    props._setPropValue(prop, self.values[prop])
            else:
                IStatusMessage(self.request).addStatusMessage(_p(u'Please correct the indicated errors'), 'error')

        for prop in self.properties:
            self.values[prop] = props.getProperty(prop, '')
        
        return self.template()
    
    @property
    @memoize
    def taxes(self):
        utils = getToolByName(self.context, 'plone_utils')
        taxes = ITaxes(self.context)
        return [{'id': utils.normalizeString(zone),
                 'zone': zone,
                 'tax': tax[0],
                 'taxname': tax[1]} for zone, tax in taxes.items()]
    
    @property 
    def taxincl(self):
        taxes = ITaxes(self.context)
        return {'tax': taxes.taxincl[0],
                'taxname': taxes.taxincl[1]}
