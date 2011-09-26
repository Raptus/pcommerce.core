import transaction
from time import time

from BTrees.OOBTree import OOBTree
from persistent import Persistent
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

from zope.event import notify
from zope.i18n import translate
from zope.interface import implements, implementer, Interface
from zope.component import adapts, adapter, getMultiAdapter, getAdapter, getAdapters
from zope.annotation.interfaces import IAnnotations

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.Portal import PloneSite

from pcommerce.core import events
from pcommerce.core.config import INITIALIZED, SENT, CANCELED, FAILED, PROCESSED
from pcommerce.core.currency import CurrencyAware
from pcommerce.core.cart import Cart
from pcommerce.core import interfaces
from pcommerce.core import PCommerceMessageFactory as _

ANNOTATIONS_KEY_ORDERS = 'pcommerce.core.orders'
ORDER_SESSION_KEY = 'pcommerce.orderid'

class Order(Persistent):
    """"""
    implements(interfaces.IOrder)
    
    state = INITIALIZED
    processed_steps = ()
    orderid = ''
    userid = ''
    products = None
    date = None
    price = 0.0
    currency = ''
    zone = None
    address = None
    shipmentids = None
    shipmentdata = None
    paymentid = None
    paymentdata = None
    pretaxcharges = None
    posttaxcharges = None
    _taxincl = None
    
    def __init__(self,
                 orderid,
                 userid,
                 price=0.0,
                 currency='',
                 date=None,
                 zone=None,
                 address=None,
                 products=[],
                 shipmentids={},
                 shipmentdata={},
                 paymentid=None,
                 paymentdata=None,
                 pretaxcharges=(),
                 posttaxcharges=(),
                 taxincl=None):
        """"""
        self.orderid = orderid
        self.userid = userid
        self.price = price
        self.currency = currency
        self.date = date
        self.zone = zone
        self.address = address
        self.products = products
        self.shipmentids = shipmentids
        self.shipmentdata = shipmentdata
        self.paymentid = paymentid
        self.paymentdata = paymentdata
        self.pretaxcharges = pretaxcharges
        self.posttaxcharges = posttaxcharges
        self._taxincl = taxincl
        
    @property
    def tax(self):
        if self.zone is None:
            return 0
        return self.zone[1][0]
    
    @property
    def taxname(self):
        if self.zone is None:
            return None
        return self.zone[1][1]
        
    @property
    def taxincl(self):
        if self._taxincl is None:
            return 0
        return self._taxincl[0]
    
    @property
    def taxinclname(self):
        if self._taxincl is None:
            return None
        return self._taxincl[1]
    
    @property
    def zonename(self):
        if self.zone is None:
            return None
        return self.zone[0]
    
    @property
    def pretaxcharge(self):
        charge = 0
        for data in self.shipmentdata.values():
            charge += getattr(data, 'pretaxcharge', 0)
        charge += getattr(self.paymentdata, 'pretaxcharge', 0)
        for data in self.pretaxcharges:
            charge += getattr(data, 'price', 0)
        return charge
    
    @property
    def posttaxcharge(self):
        charge = 0
        for data in self.shipmentdata.values():
            charge += getattr(data, 'posttaxcharge', 0)
        charge += getattr(self.paymentdata, 'posttaxcharge', 0)
        for data in self.posttaxcharges:
            charge += getattr(data, 'price', 0)
        return charge
    
    @property
    def subtotal(self):
        return self.price + self.pretaxcharge
    
    @property
    def pricetax(self):
        return self.subtotal * self.tax / 100
    
    @property
    def pricetaxincl(self):
        return self.subtotal / 100 * self.taxincl
    
    @property
    def total(self):
        return self.subtotal + self.pricetax
    
    @property
    def totalincl(self):
        return self.total + self.posttaxcharge

class OrderRegistry(Cart):
    """"""
    implements(interfaces.IOrderRegistry)
    adapts(Interface)
    
    def __init__(self, context):
        self.context = context
        self.portal = context
        if not isinstance(context, PloneSite):
            self.portal = getMultiAdapter((self.context, self.context.REQUEST), name=u'plone_portal_state').portal()
    
    @property
    def _items(self):
        annotations = IAnnotations(self.portal)
        items = annotations.get(ANNOTATIONS_KEY_ORDERS, OOBTree())
        # BBB
        if not isinstance(items, OOBTree):
            btree_items = OOBTree()
            for key, value in items:
                btree_items[key] = value
            items = btree_items
        return items
        
    def getOrders(self):
        """ returns a list of orders
        """
        return self._items
    
    def getOrder(self, orderid):
        """ returns a order by its id
        """
        if not self.has_key(orderid):
            return None
        return self[orderid]
    
    def create(self, order):
        """ generates an order from the cart
        """
        member = getMultiAdapter((self.context, self.context.REQUEST), name=u'plone_portal_state').member()
        cart = interfaces.IShoppingCart(self.context)
        if not len(cart):
            return
        order.userid = member.getId()
        order.date = time()
        order.currency = CurrencyAware(0).getCurrencySymbol()
        products = cart.getProducts()
        order_products = PersistentList()
        price = 0
        for product in products:
            price += product['price_raw'] * product['amount']
            order_products.append((product['uid'],
                                   product['no'],
                                   product['title'],
                                   product['amount'],
                                   product['price_raw'],
                                   [(variation['uid'], variation['type'], variation['name']) for variation in product['variations']]))
        if order_products != order.products:
            order.processed_steps = ()
        order.products = order_products
        order.price = price
        
        order._taxincl = interfaces.ITaxes(self.context).taxincl
        
        pretaxcharges = []
        providers = getAdapters((self.context,), interfaces.IPreTaxCharge)
        for name, provider in providers:
            pretaxcharges.append(provider.process(order))
        order.pretaxcharges = tuple(pretaxcharges)
        
        posttaxcharges = []
        providers = getAdapters((self.context,), interfaces.IPostTaxCharge)
        for name, provider in providers:
            posttaxcharges.append(provider.process(order))
        order.posttaxcharges = tuple(posttaxcharges)
        
        self[order.orderid] = order
        
    def recover(self, orderid):
        """ recover an order from the registry
        """
        if not self.has_key(orderid):
            return
        order = self[orderid]
        cart = interfaces.IShoppingCart(self.context)
        cart.clear()
        for uid, title, price_raw, amount, variations in order.products:
            if variations:
                cart.addVariation([uid for uid, type, name in variations], amount)
            else:
                cart.add(uid, amount)
        
        notify(events.OrderRecoveredEvent(self, order))
        
    def send(self, orderid, lang=None):
        """ sends an order
        """
        request = self.context.REQUEST
        if not self.has_key(orderid):
            return
        order = self[orderid]
        if order.state >= SENT:
            if order.orderid == request.SESSION.get(ORDER_SESSION_KEY, 0):
                request.SESSION.set(ORDER_SESSION_KEY, None)
            return
        portal_state = getMultiAdapter((self.context, request), name=u'plone_portal_state')
        address = order.address
        shipments = []
        shipments_customer = []
        product_shipment = {}
        id_shipment = {}
        i = 1
        for shipmentid, products in order.shipmentids.items():
            shipment = getAdapter(self.context, name=shipmentid, interface=interfaces.IShipmentMethod)
            info = translate(shipment.mailInfo(order), context=request, target_language=lang)
            if len(order.shipmentids) > 1:
                info = '(%s) %s' % (i, info)
            shipments.append(info)
            
            info_customer = translate(shipment.mailInfo(order, lang, customer=True), context=request, target_language=lang)
            if len(order.shipmentids) > 1:
                info = '(%s) %s' % (i, info_customer)
            shipments_customer.append(info_customer)
            
            for product in products:
                product_shipment[product] = i
            id_shipment[shipmentid] = {'title': shipment.title,
                                       'number': i}
            i += 1
        
        payment = getAdapter(self.context, name=order.paymentid, interface=interfaces.IPaymentMethod)
        alignment = Alignment()
        
        cart = []
        cart.append([translate(_('Product'), context=request, target_language=lang),
                     translate(_('Amount'), context=request, target_language=lang),
                     translate(_('Price'), context=request, target_language=lang),
                     translate(_('Price total'), context=request, target_language=lang)])
        cart.extend(['-', ''])
        
        for product in order.products:
            cart.append([len(order.shipmentids) > 1 and '%s (%s)' % (product[1], product_shipment[product[0]]) or product[1],
                         str(product[3]),
                         ">"+CurrencyAware(product[4]).valueToString(order.currency),
                         ">"+CurrencyAware(product[4] * product[3]).valueToString(order.currency)])
            cart.append(product[2].decode('utf-8'))
            for variation in product[5]:
                cart.append("\t%s: %s" % (variation[1].decode('utf-8'), variation[2].decode('utf-8')))
            cart.append("")
        
        cart.append('-')
        cart.append(['%s:' % translate(_('Total'), context=request, target_language=lang), '', '',
                     ">"+CurrencyAware(order.price).valueToString(order.currency)])
        cart.extend(['-', ''])
            
        if order.pretaxcharge:
            if order.paymentdata.pretaxcharge:
                cart.append(['%s:' % translate(payment.title, context=request, target_language=lang), '', '',
                             ">"+CurrencyAware(order.paymentdata.pretaxcharge).valueToString(order.currency)])
            for shipmentid, data in order.shipmentdata.items():
                if data.pretaxcharge:
                    cart.append(['%s:' % (len(order.shipmentids) > 1 and '%s (%s)' % (translate(id_shipment[shipmentid]['title'], context=request, target_language=lang), id_shipment[shipmentid]['number']) or translate(id_shipment[shipmentid]['title'], context=request, target_language=lang)), '', '',
                                 ">"+CurrencyAware(data.pretaxcharge).valueToString(order.currency)])
            for charge in order.pretaxcharges:
                if charge.price:
                    cart.append(['%s:' % translate(charge.title, context=request, target_language=lang), '', '',
                                 ">"+CurrencyAware(charge.price).valueToString(order.currency)])
            cart.append('-')
            cart.append(['%s:' % translate(_('Total incl. charges'), context=request, target_language=lang), '', '',
                         ">"+CurrencyAware(order.subtotal).valueToString(order.currency)])
            cart.extend(['-', ''])
        
        if order.tax:
            cart.append([order.taxname, '', '',
                         '%(pricetax)s (%(tax)s %% - %(zone)s)' % dict(tax=order.tax,
                                                                       pricetax=">"+CurrencyAware(order.pricetax).valueToString(order.currency),
                                                                       zone=address.zone)])
            cart.append('-')
            cart.append(['%s:' % translate(_('Total incl. ${taxname}', mapping=dict(taxname=order.taxname)), context=request, target_language=lang), '', '',
                         ">"+CurrencyAware(order.total).valueToString(order.currency)])
            cart.extend(['-', ''])
        
        if order.taxincl and order.posttaxcharge is None:
            cart.append([order.taxname, '', '',
                         '%(pricetax)s (%(tax)s %% - %(zone)s)' % dict(tax=order.tax,
                                                                       pricetax=">"+CurrencyAware(order.pricetax).valueToString(order.currency),
                                                                       zone=address.zone)])
            cart.append('-')
            cart.append(['%s:' % translate(_('Total incl. ${tax}% ${taxname}', mapping=dict(tax=order.taxincl, taxname=order.taxinclname)), context=request, target_language=lang), '', '',
                             ">"+CurrencyAware(order.totalincl).valueToString(order.currency)])
            cart.extend(['-', ''])
            
            
        if order.posttaxcharge:
            if order.paymentdata.posttaxcharge:
                cart.append(['%s:' % translate(payment.title, context=request, target_language=lang), '', '',
                             ">"+CurrencyAware(order.paymentdata.posttaxcharge).valueToString(order.currency)])
            for shipmentid, data in order.shipmentdata.items():
                if data.posttaxcharge:
                    cart.append(['%s:' % (len(order.shipmentids) > 1 and '%s (%s)' % (translate(id_shipment[shipmentid]['title'], context=request, target_language=lang), id_shipment[shipmentid]['number']) or translate(id_shipment[shipmentid]['title'], context=request, target_language=lang)), '', '', 
                                 ">"+CurrencyAware(data.posttaxcharge).valueToString(order.currency)])
            for charge in order.posttaxcharges:
                if charge.price:
                    cart.append(['%s:' % translate(charge.title, context=request, target_language=lang), '', '',
                                 ">"+CurrencyAware(charge.price).valueToString(order.currency)])
            cart.append('-')
            if order.tax:
                cart.append(['%s:' % translate(_('Total incl. charges and ${taxname}', mapping=dict(taxname=order.taxname)), context=request, target_language=lang), '', '',
                             ">"+CurrencyAware(order.totalincl).valueToString(order.currency)])
            elif order.taxincl:
                cart.append(['%s:' % translate(_('Total incl. charges and ${tax}% ${taxname}', mapping=dict(tax=order.taxincl, taxname=order.taxinclname)), context=request, target_language=lang), '', '',
                             ">"+CurrencyAware(order.totalincl).valueToString(order.currency)])
            else:
                cart.append(['%s:' % translate(_('Total incl. charges'), context=request, target_language=lang), '', '',
                             ">"+CurrencyAware(order.totalincl).valueToString(order.currency)])
            cart.extend(['-', ''])
    
        alignment.extend(cart)
        
        # do alignment
        cart = alignment.alignItems(cart)
           
        email_from = portal_state.portal().getProperty('email_from_address', '')
        email_from_name = portal_state.portal().getProperty('email_from_name', '')
        mapping = {'orderid': order.orderid,
                   'shipments': '\n\n'.join(shipments),
                   'payment': translate(payment.mailInfo(order, lang), context=request, target_language=lang),
                   'cart': '\n'.join(cart),
                   'currency': order.currency,
                   'address': address.mailInfo(request, lang),
                   'name': address.firstname +' '+ address.lastname,
                   'from_name': email_from_name,
                   'from_email': email_from}

        mailhost = getToolByName(self.context, 'MailHost')
        mailhost.secureSend(translate(self.getMessage(mapping), context=request, target_language=lang),
                            mto=email_from,
                            mfrom='%s <%s>' % (address.firstname +' '+ address.lastname, address.email),
                            subject=translate(_('email_order_title', default='New order [${orderid}]', mapping={'orderid': order.orderid}), context=request, target_language=lang),
                            charset='utf-8')
        
        mapping.update({'shipments': '\n\n'.join(shipments_customer),
                        'payment': translate(payment.mailInfo(order, lang, customer=True), context=request, target_language=lang),
                        'address': address.mailInfo(request, lang, True)})
        mailhost.secureSend(translate(self.getMessageCustomer(mapping), context=request, target_language=lang),
                            mto='%s <%s>' % (address.firstname +' '+ address.lastname, address.email),
                            mfrom='%s <%s>' % (email_from_name, email_from),
                            subject=translate(_('email_customer_title', default='Confirmation Email'), context=request, target_language=lang),
                            charset='utf-8')
        
        notify(events.OrderSentEvent(self, order))
        
        order.state = SENT
        if order.orderid == request.SESSION.get(ORDER_SESSION_KEY, 0):
            request.SESSION.set(ORDER_SESSION_KEY, None)
        
    def process(self, orderid):
        """ process an order
        """
        if not self.has_key(orderid):
            return
        order = self[orderid]
        
        notify(events.OrderProcessedEvent(self, order))
        
        order.state = PROCESSED
        if order.orderid == self.context.REQUEST.SESSION.get(ORDER_SESSION_KEY, 0):
            self.context.REQUEST.SESSION.set(ORDER_SESSION_KEY, None)
        
    def cancel(self, orderid):
        """ cancel an order
        """
        if not self.has_key(orderid):
            return
        order = self[orderid]
        
        notify(events.OrderCanceledEvent(self, order))
        
        order.state = CANCELED
        if order.orderid == self.context.REQUEST.SESSION.get(ORDER_SESSION_KEY, 0):
            self.context.REQUEST.SESSION.set(ORDER_SESSION_KEY, None)
        
    def fail(self, orderid):
        """ fail an order
        """
        if not self.has_key(orderid):
            return
        order = self[orderid]
        
        notify(events.OrderFailedEvent(self, order))
        
        order.state = FAILED
        if order.orderid == self.context.REQUEST.SESSION.get(ORDER_SESSION_KEY, 0):
            self.context.REQUEST.SESSION.set(ORDER_SESSION_KEY, None)
        
    def getMessage(self, mapping):
        return _('email_order_body', default=\
"""New order by ${name}

Orderid: ${orderid}

${cart}
Currency: ${currency}


Address:
${address}

Payment:
${payment}

Shipment:
${shipments}

""", mapping=mapping)
        
    def getMessageCustomer(self, mapping):
        return _('email_customer_body', default=\
"""Dear ${name}

Your order has successfully been registered. Please find a complete
overview of your order below.

Order ID: ${orderid}

${cart}
Currency: ${currency}


Address:
${address}

Payment:
${payment}

Shipment:
${shipments}


If you have any questions concerning your purchase do not hesitate
to contact us at ${from_email}.

Best regards

${from_name}
""", mapping=mapping)
    
    def _save(self):
        annotations = IAnnotations(self.portal)
        annotations[ANNOTATIONS_KEY_ORDERS] = self._items
        
class Alignment(object):
    
    separate = 4
    rows = []
    
    def align(self, item):
        if not isinstance(item, list):
            if item.startswith('-'):
                return '-' * len(self)
            return item
        aligned = []
        for i in range(0, len(item)):
            import pdb; pdb.set_trace
            if item[i].startswith('>'):
                item[i] = item[i][1:]
                aligned.append((' ' * (self.max(i) - len(item[i]))) + item[i])
            else:
                aligned.append(item[i] + (' ' * (self.max(i) - len(item[i]))))
        return (' ' * self.separate).join(aligned)
    
    def alignItems(self, items):
        return [self.align(item) for item in items]
        
    def append(self, item):
        self.rows.append(item)
        
    def extend(self, items):
        self.rows.extend(items)
        
    def max(self, i):
        return max([len(row[i]) for row in self.rows if isinstance(row, list) and len(row) > i])
        
    def __len__(self):
        l = 0
        for i in range(0, max([len(row) for row in self.rows if isinstance(row, list)])):
            l += self.max(i)
        l += i * self.separate
        return l

@adapter(Interface)
@implementer(interfaces.IOrder)
def get_order(context):
    orderid = context.REQUEST.SESSION.get(ORDER_SESSION_KEY, 0)
    order = None
    orders = interfaces.IOrderRegistry(context)
    if orderid and orders.has_key(orderid):
        order = orders[orderid]
        if order.state is INITIALIZED:
            notify(events.OrderAboutToBeRecreatedEvent(orders, order))
            orders.create(order)
            notify(events.OrderRecreatedEvent(orders, order))
        else:
            order = None

    if not order:
        orderid = int(time()*100)
        context.REQUEST.SESSION.set(ORDER_SESSION_KEY, orderid)
        order = Order(orderid, None)
        orders.create(order)
        
        notify(events.OrderCreatedEvent(orders, order))
    
    return order
