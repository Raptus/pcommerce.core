import re

from zope.component import getMultiAdapter
from zope.interface import implements

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from Products.validation.validators.BaseValidators import EMAIL_RE
email_re = re.compile(EMAIL_RE)

from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.config import INITIALIZED
from pcommerce.core.interfaces import IShoppingCart, IOrderRegistry, ISteps
from pcommerce.core.interfaces import ICheckoutView, IComponent, IOrder

from pcommerce.core.order import ORDER_SESSION_KEY


class Checkout(BrowserView):
    """checkout view
    """
    implements(ICheckoutView)

    template = ViewPageTemplateFile('checkout.pt')

    errors = {}
    cart = None
    order = None
    stepid = 0
    components = []
    redirect = None

    def __call__(self):
        self.request.set('disable_border', 1)
        self.errors = {}

        self.cart = IShoppingCart(self.context)

        if not len(self.cart):
            statusmessage = IStatusMessage(self.request)
            statusmessage.addStatusMessage(_(u'You have not yet added any '
                'products to your cart'), 'error')
            return self.request.RESPONSE.redirect('%s/@@cart' %
                    self.context.absolute_url())

        if self.request.form.get('checkout.cancel', None):
            return getMultiAdapter((self.context, self.request),
                    name=u'checkout.cancel')()

        self.stepid = int(self.request.form.get('checkout.stepid', 0))

        temp_state = None
        registry = IOrderRegistry(self.context)
        self.order = registry.getOrder(self.request.SESSION.get(
            ORDER_SESSION_KEY, 0))
        if self.order is not None and self.order.state != INITIALIZED:
            temp_state = self.order.state
            self.order.state = INITIALIZED

        self.order = IOrder(self.context)

        self._stepid_validator()

        if self.request.form.get('checkout.next') and \
            self.stepid < len(self.steps) - 1:
            self.next()
        elif self.request.form.get('checkout.previous') and self.stepid > 0:
            self.previous()
        elif self.request.get('stepid'):
            self.gotostep(int(self.request.get('stepid', 0)))

        if self.redirect is not None:
            return self.request.RESPONSE.redirect(self.redirect)

        html = self.template()

        if temp_state is not None:
            self.order.state = temp_state

        if self.laststep:
            registry = IOrderRegistry(self.context)
            registry.send(self.order.orderid)
            self.cart.clear()
        return html

    @property
    def steps(self):
        return ISteps(self.context)

    def next(self):
        self._nextstep()
        while 1:
            for component in self.components:
                if component.renders():
                    return
            self._nextstep()

    def previous(self):
        self._previousstep()
        while 1:
            for component in self.components:
                if component.renders():
                    return
            self._previousstep()

    def gotostep(self, stepid):
        self._gotostep(stepid)
        renders = False
        for component in self.components:
            if component.renders():
                renders = True
        if not renders:
            self.gotostep(self.stepid + 1)

    def _nextstep(self):
        if self.validate():
            self.process()
            self.stepid += 1
            self._stepid_validator()

    def _previousstep(self):
        self.stepid -= 1
        self._stepid_validator()

    def _gotostep(self, stepid):
        self.stepid = stepid
        self._stepid_validator()

    def _stepid_validator(self):
        if self.stepid < 0:
            self.stepid = 0
            self._initialize_components()
            return
        elif self.stepid > len(self.steps) - 1:
            self.stepid = len(self.steps) - 1

        for stepid in range(0, self.stepid):
            if not stepid in self.order.processed_steps:
                self.stepid = stepid
                self._initialize_components()
                return

        self._initialize_components()

    def _initialize_components(self):
        self.components = []
        for name in self.steps[self.stepid]['components']:
            component = getMultiAdapter((self.context, self.request),
                    interface=IComponent, name=name).__of__(self.context)
            self.components.append(component)
        return self.components

    def validate(self):
        valid = True
        for component in self.components:
            if not component.validate():
                valid = False
        return valid

    def process(self):
        self.redirect = None
        for component in self.components:
            component.process()
            if not (self.stepid in self.order.processed_steps):
                self.order.processed_steps = self.order.processed_steps + \
                (self.stepid,)
            for i in range(0, len(self.steps)):
                step = self.steps[i]
                for name in step['components']:
                    s_component = getMultiAdapter(
                            (self.context, self.request), interface=IComponent,
                            name=name).__of__(self.context)
                    if component.__name__ in s_component.dependencies:
                        self.order.processed_steps = \
                        tuple([n for n in self.order.processed_steps
                            if not n == i])
            if hasattr(component, 'action'):
                action = component.action()
                if action:
                    self.redirect = action

    def renders(self, step):
        components = []
        for name in step['components']:
            component = getMultiAdapter((self.context, self.request),
                    interface=IComponent, name=name).__of__(self.context)
            if component.renders():
                return True
        return False

    @property
    def stepnavigation(self):
        steps = []
        step = None

        for i in range(0, len(self.steps)):
            step = self.steps[i]
            if len(steps) and step['name'] == steps[-1]['name']:
                continue
            renders = False
            for name in step['components']:
                component = getMultiAdapter((self.context, self.request),
                        interface=IComponent, name=name).__of__(self.context)
                if component.renders():
                    renders = True
            if not renders:
                continue

            selected = False
            if step['name'] == self.steps[self.stepid]['name']:
                selected = True

            _class = 'step'
            if i == 0:
                _class += ' first'
            elif i == (len(self.steps) - 1):
                _class += ' last'
            if selected:
                _class += ' select'
            if i < self.stepid:
                _class += ' passed'
            if i in self.order.processed_steps:
                _class += ' processed'
            href = None
            if (i in self.order.processed_steps or \
                    (i - 1) in self.order.processed_steps) and \
                    not selected and not self.laststep:
                href = '%s/@@checkout?stepid=%s' % (
                        self.context.absolute_url(), i)

            steps.append({'stepid': str(i),
                          'name': step['name'],
                          'selected': selected,
                          'href': href,
                          'class': _class, })
        return steps

    @property
    def previous_label(self):
        for component in self.components:
            if hasattr(component, 'previous_label'):
                return component.previous_label
        if self.laststep:
            return _(u'Print')
        return _(u'Previous step')

    @property
    def next_label(self):
        for component in self.components:
            if hasattr(component, 'next_label'):
                return component.next_label
        if self.laststep:
            return _(u'Continue shopping')
        if self.stepid == len(self.steps) - 2:
            return _(u'Send order')
        return _(u'Next step')

    @property
    def cancel_label(self):
        for component in self.components:
            if hasattr(component, 'cancel_label'):
                return component.cancel_label
        return _(u'Cancel checkout')

    @property
    def previous_onclick(self):
        for component in self.components:
            if hasattr(component, 'previous_onclick'):
                return component.previous_onclick
        if self.laststep:
            return "print()"
        return None

    @property
    def next_onclick(self):
        for component in self.components:
            if hasattr(component, 'next_onclick'):
                return component.next_onclick
        return None

    @property
    def cancel_onclick(self):
        for component in self.components:
            if hasattr(component, 'cancel_onclick'):
                return component.cancel_onclick
        return None

    @property
    def action(self):
        if self.laststep:
            props = getToolByName(self.context,
                    'portal_properties').pcommerce_properties
            portal_state = getMultiAdapter((self.context, self.request),
                    name=u'plone_portal_state')
            return '%s/%s' % (portal_state.portal_url(),
                    props.getProperty('post_checkout', ''))
        return self.context.absolute_url() + '/@@checkout'

    @property
    def laststep(self):
        return self.stepid == len(self.steps) - 1


class PaymentFailed(BrowserView):
    """ Payment failed
    """

    def __call__(self):
        order = IOrder(self.context)
        m = len(order.processed_steps) and max(order.processed_steps) or 0
        order.processed_steps = tuple(
                [n for n in order.processed_steps if n != m])
        statusmessage = IStatusMessage(self.request)
        statusmessage.addStatusMessage(_(u'Payment failed'), 'error')
        return self.request.RESPONSE.redirect('%s/@@checkout?stepid=%s' % (
            self.context.absolute_url(), m))


class PaymentCancel(BrowserView):
    """ Payment canceled
    """

    def __call__(self):
        order = IOrder(self.context)
        m = len(order.processed_steps) and max(order.processed_steps) or 0
        order.processed_steps = tuple(
                [n for n in order.processed_steps if n != m])
        statusmessage = IStatusMessage(self.request)
        statusmessage.addStatusMessage(_(u'Payment canceled'), 'error')
        return self.request.RESPONSE.redirect('%s/@@checkout?stepid=%s' % (
            self.context.absolute_url(), m))


class PaymentSuccess(BrowserView):
    """ Payment successful
    """

    def __call__(self):
        registry = IOrderRegistry(self.context)
        order = registry.getOrder(
                self.request.SESSION.get(ORDER_SESSION_KEY, 0))
        return self.request.RESPONSE.redirect(
                '%s/@@checkout?checkout.stepid=%s' % (
                    self.context.absolute_url(),
                    max(order.processed_steps) + 1))


class CheckoutCancel(BrowserView):
    """checkout cancel view
    """

    def __call__(self):
        registry = IOrderRegistry(self.context)
        registry.cancel(self.request.SESSION.get(ORDER_SESSION_KEY, 0))
        statusmessage = IStatusMessage(self.request)
        statusmessage.addStatusMessage(
                _('message_checkout_canceled', default=u'Check out canceled'),
                'info')
        return self.request.RESPONSE.redirect('%s/@@cart' %
                self.context.absolute_url())


class CheckoutFailed(BrowserView):
    """checkout failed view
    """

    def __call__(self):
        registry = IOrderRegistry(self.context)
        registry.fail(self.request.SESSION.get(ORDER_SESSION_KEY, 0))
        statusmessage = IStatusMessage(self.request)
        statusmessage.addStatusMessage(_('message_checkout_failed',
            default=u'Check out failed'), 'error')
        return self.request.RESPONSE.redirect(
                '%s/@@cart' % self.context.absolute_url())
