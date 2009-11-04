import re
from Acquisition import aq_inner, aq_parent

from zope.component import getMultiAdapter, getUtility
from zope.interface import implements
from zope.i18n import translate

from Products.statusmessages.interfaces import IStatusMessage

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from plone.memoize.instance import memoize

from Products.CMFPlone import PloneMessageFactory as _p

from Products.validation.validators.BaseValidators import EMAIL_RE
email_re = re.compile(EMAIL_RE)

from pcommerce.core.config import INITIALIZED, SENT, CANCELED, FAILED
from pcommerce.core.address import Address
from pcommerce.core.interfaces import IShoppingCart, IOrderRegistry, IPaymentRegistry, ITaxes
from pcommerce.core.currency import CurrencyAware
from pcommerce.core import PCommerceMessageFactory as _

class CheckoutBaseView(BrowserView):
    """
    """
    payment_method = None
    payment_id = None
    
    def __call__(self):
        self.request.set('disable_border', True)
        
        payments = self.getPayments()
        payment_id = None
        if len(payments) == 1:
            payment_id = payments.keys()[0]
        elif self.request.form.get('payment_id', None) is not None:
            payment_id = self.request.form.get('payment_id', None)
            self.request.SESSION.set('pcommerce.payment_id', payment_id)
        elif self.request.SESSION.get('pcommerce.payment_id', None) is not None:
            payment_id = self.request.SESSION.get('pcommerce.payment_id', None)
        if payment_id is not None and payments.has_key(payment_id):
            self.payment_id = payment_id
        if self.payment_id is not None:
            self.payment_method = payments[self.payment_id]
    
    @memoize
    def getPayments(self):
        registry = getUtility(IPaymentRegistry)
        return registry.getPaymentMethods()
    
    @property
    @memoize
    def payments(self):
        payments = []
        for name, payment in self.getPayments().items():
            payments.append({'id': name,
                             'title': payment.title,
                             'description': payment.description,
                             'icon': payment.icon,
                             'logo': payment.logo})
        return payments
        
    def _resetSession(self):
        self.request.SESSION.set('pcommerce.payment_id', 0)

class CheckoutView(CheckoutBaseView):
    """checkout view
    """
    cart = None
    order = None
    required = ('name', 'address1', 'city', 'country','gtc',)
    fields = ('name', 'address1', 'address2', )
    errors = {}

    template = ViewPageTemplateFile('templates/checkout.pt')
    template_pre = ViewPageTemplateFile('templates/checkout_pre.pt')
    template_info = ViewPageTemplateFile('templates/checkout_info.pt')
    template_post = ViewPageTemplateFile('templates/checkout_post.pt')
    
    def __call__(self):
        CheckoutBaseView.__call__(self)
        self.errors = {}
        self.order = None
        
        self.cart = IShoppingCart(self.context)
        if not len(self.cart):
            statusmessage = IStatusMessage(self.request)
            statusmessage.addStatusMessage(_(u'You have not yet added any products to your cart'), 'error')
            return self.request.RESPONSE.redirect('%s/@@cart' % self.context.absolute_url())
                
        if self.request.form.get('pcommerce.cancel', None):
            return getMultiAdapter((self.context, self.request), name=u'checkout.cancel')()
 
        if self.payment_method is not None:
            
            # get the orderid from the payment method
            orderid = self.payment_method.getOrderId(self.context)
            
            # get the order
            orders = IOrderRegistry(self.context)
            if orderid and orders.has_key(orderid):
                self.order = orders[orderid]
                if self.order.state is INITIALIZED:
                    orders.create(self.order, self.order.delivery.zone)
                else:
                    self.order = None
            
            if self.request.form.get('pcommerce.checkout', None) and self.order:
                orders.send(self.order.orderid)
                self.payment_method.checkout(self.context, self.order)
                self.cart.clear()
                return self.template_post()
                
            # render pre payment page
            if self.request.get('pcommerce.pre', None) is not None:
                if not self.pre_payment:
                    return self.template_info()
                if self.request.get('pcommerce.pre.edit', None):
                    if self.pre_payment.validate(self.order):
                        self.pre_payment.process(self.order)
                        return self.template_info()
                    statusmessage = IStatusMessage(self.request)
                    statusmessage.addStatusMessage(_p(u'Please correct the indicated errors'), 'error')
                return self.template_pre()
            
            # render delivery page
            if self.request.form.get('pcommerce.delivery', None) is not None:
                if self.request.get('pcommerce.delivery.edit', None):
                    if self.validate():
                        if not self.order or self.order.state is not INITIALIZED:
                            self.payment_method.startCheckout(self.context)
                            self.order = self.payment_method.getOrder(self.context)
                        self.order.delivery = Address(name=self.request.get('name').decode('utf-8'),
                                                      address1=self.request.get('address1').decode('utf-8'),
                                                      address2=self.request.get('address2').decode('utf-8'),
                                                      zip=self.request.get('zip').decode('utf-8'),
                                                      city=self.request.get('city').decode('utf-8'),
                                                      country=self.request.get('country').decode('utf-8'),
                                                      zone=self.request.get('zone', '').decode('utf-8'),
                                                      email=self.request.get('email').decode('utf-8'),
                                                      phone=self.request.get('phone'))
                        orders[self.payment_method.getOrderId(self.context)] = self.order
                        if self.pre_payment:
                            self.request.form = {}
                            return self.template_pre()
                        return self.template_info()
                    statusmessage = IStatusMessage(self.request)
                    statusmessage.addStatusMessage(_p(u'Please correct the indicated errors'), 'error')
            
        return self.template()
    
    def validate(self):
        if self.request.get('as_delivery', 0):
            if self.order.delivery:
                return True
        for field in self.required:
            if not self.request.get(field, ''):
                self.errors[field] = _p(u'This field is required, please provide some information.')
        if self.request.get('email', 0):
            if not email_re.match(self.request.get('email', '')):
                self.errors['email'] = _p(u'Please submit a valid email address.')
        return len(self.errors) == 0
    
    @property
    @memoize
    def amount(self):
        return self.cart.amount()
    
    @property
    @memoize
    def products(self):
        return self.cart.getProducts()
    
    @property
    @memoize
    def price(self):
        if self.order:
            return CurrencyAware(self.order.price)
        return CurrencyAware(self.cart.getPrice())
    
    @property
    @memoize
    def price_tax(self):
        if self.order:
            return CurrencyAware(self.order.price_tax)
        return None
    
    @property
    @memoize
    def tax(self):
        if self.order:
            return self.order.tax
        return None
    
    @property
    @memoize
    def total(self):
        if self.order:
            return CurrencyAware(self.order.total)
        return None
    
    @property
    @memoize
    def zones(self):
        taxes = ITaxes(self.context)
        return [{'name': name,
                 'tax': tax} for name, tax in taxes.items()]
            
    @memoize
    def gtc(self):
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        return '%s/%s' % (getToolByName(self.context, 'portal_url')(), props.getProperty('gtc', ''))
    
    @memoize
    def getDescription(self):
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        return props.getProperty('productname', self.context.Title())
        
    @property
    @memoize
    def pre_payment(self):
        if self.payment_method is not None and self.payment_method.pre_view_name:
            return getMultiAdapter((self.context, self.request), name=self.payment_method.pre_view_name)
        return None
        
    @property
    @memoize
    def info_payment(self):
        if self.payment_method is not None and self.payment_method.info_view_name:
            return getMultiAdapter((self.context, self.request), name=self.payment_method.info_view_name)
        return None
        
    @property
    @memoize
    def post_payment(self):
        if self.payment_method is not None and self.payment_method.post_view_name:
            return getMultiAdapter((self.context, self.request), name=self.payment_method.post_view_name)
        return None
        
    @property
    @memoize
    def post_payment_type(self):
        if not self.post_payment:
            return None
        return IPaymentFormView.providedBy(self.post_payment)
    
    @property
    @memoize
    def member_info(self):
        mship = getToolByName(self.context, 'portal_membership')
        return mship.getMemberInfo()
    
    @memoize
    def getOrderId(self):
        return self.payment_method.getOrderId(self.context)

class CheckoutCancelView(CheckoutBaseView):
    """checkout cancel view
    """

    def __call__(self):
        CheckoutBaseView.__call__(self)
        
        if self.payment_method is not None:
            registry = IOrderRegistry(self.context)
            orderid = self.payment_method.getOrderId(self.context)
            if registry.has_key(orderid):
                order = registry[orderid]
                order.state = CANCELED
                self.payment_method.cancelCheckout(self.context, order)
                registry.recover(orderid)
        statusmessage = IStatusMessage(self.request)
        statusmessage.addStatusMessage(_('message_checkout_canceled', default=u'Check out canceled'), 'info')
        self._resetSession()
        return self.request.RESPONSE.redirect('%s/@@cart' % self.context.absolute_url())
    
class CheckoutFailedView(CheckoutBaseView):
    """checkout failed view
    """

    def __call__(self):
        CheckoutBaseView.__call__(self)
        
        if self.payment_method is not None:
            registry = IOrderRegistry(self.context)
            orderid = self.payment_method.getOrderId(self.context)
            if registry.has_key(orderid):
                order = registry[orderid]
                order.state = FAILED
                self.payment_method.cancelCheckout(self.context, order)
                registry.recover(orderid)
        statusmessage = IStatusMessage(self.request)
        statusmessage.addStatusMessage(_('message_checkout_failed', default=u'Check out failed'), 'error')
        self._resetSession()
        return self.request.RESPONSE.redirect('%s/@@cart' % self.context.absolute_url())