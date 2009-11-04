from time import time

from Acquisition import aq_parent
from AccessControl import Unauthorized

from persistent.dict import PersistentDict

from zope.interface import implements, Interface
from zope.component import adapts, getMultiAdapter
from zope.event import notify
from zope.i18n import translate

from zope.annotation.interfaces import IAnnotations

from Products.CMFCore.utils import getToolByName

from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.config import AddToCart, PROCESSED, FAILED, SENT
from pcommerce.core.interfaces import IProduct, IPrice, IVariation, IPricing, IImaging, IShoppingCart, ITaxes, IOrderRegistry, IPaymentProcessor
from Products.ATContentTypes.interface.image import IImageContent
from pcommerce.core.currency import CurrencyAware
from pcommerce.core.events import OrderProcessedEvent, OrderProcessingFailedEvent

SESSION_KEY = 'pcommerce.core.cart'
ANNOTATIONS_KEY_ORDERS = 'pcommerce.core.orders'
ANNOTATIONS_KEY_TAXES = 'pcommerce.core.taxes'

class Cart(object):
    """
    """
    _items = {}
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, key):
        return self._items[key]
    
    def __setitem__(self, key, value):
        if key:
            self._items[key] = value
            self._save()
    
    def has_key(self, key):
        return self._items.has_key(key)
    
    def items(self):
        return self._items.items()
        
class ShoppingCart(Cart):
    """ An adapter to handle a shopping cart
    
        the adapter supports the following stanard python methods:
        
        len(ShoppingCart)
        ShoppingCart.has_key(key)
        ShoppingCart.items()
        ShoppingCart[key]
        ShoppingCart[key] = value
        del(ShoppingCart[key])
    """
    implements(IShoppingCart)
    
    def __init__(self, context):
        self.context = context
        self._items = self.context.REQUEST.SESSION.get(SESSION_KEY, {})
    
    def __delitem__(self, key):
        del(self._items[key])
        self._save()
    
    def amount(self):
        """ returns amount of products in the cart
        """
        size = 0
        for uid, amount in self.items():
            size += amount
        return size
    
    def getPrice(self):
        """ returns the total price of all products in the cart
        """
        price = 0
        products = self.getProducts()
        for product in products:
            price += product['price_total_raw']
        return price
    
    def getProducts(self):
        """ returns list of products currently in the cart
        """
        catalog = getToolByName(self.context, 'uid_catalog')
        products = []
        for uid, amount in self.items():
            results = [product.getObject() for product in catalog(object_provides=IProduct.__identifier__, UID=uid)]
            if results:
                price = 0
                add_price = 0
                variations = []
                product = None
                for result in results:
                    adapter = IPricing(result)
                    cprice = adapter.getPrice()
                    if IVariation.providedBy(result):
                        variation = {'type': result.getType(),
                                     'name': result.Title(),
                                     'no': result.getNo(),
                                     'add_price': None,
                                     'add_price_raw': None,
                                     'uid': result.UID(),
                                     'object': result}
                        if result.getAddPrice():
                            variation['add_price_raw'] = float(result.getPrice())
                            variation['add_price'] = CurrencyAware(result.getPrice())
                            add_price += float(result.getPrice())
                        variations.append(variation)
                        if not product:
                            product = aq_parent(result)
                    else:
                        product = result
                    if cprice > price:
                        price = cprice
                products.append({'title': product.Title(),
                                 'no': product.getNo(),
                                 'description': product.Description(),
                                 'price': CurrencyAware(price + add_price),
                                 'price_raw': price + add_price,
                                 'price_total': CurrencyAware((price + add_price) * amount),
                                 'price_total_raw': (price + add_price) * amount,
                                 'uid': product.UID(),
                                 'amount': amount,
                                 'url': product.absolute_url(),
                                 'variations': variations,
                                 'object': product
                                })
        return products
    
    def addVariation(self, item, amount=1):
        """ adds a variation of a product to the cart
        
            possible values of item:
            - a uid
            - a list of uids (combination of  multiple variations)
        """
        uids = getToolByName(self.context, 'uid_catalog').uniqueValuesFor('UID')
        if not isinstance(item, basestring):
            item.sort()
            for i in item:
                if not i in uids:
                    return 0
            item = tuple(item)
        elif not item in uids:
            return 0
            
        return self._addItem({'uid': item,
                              'amount': int(amount)})
    
    def add(self, items, amount=1):
        """ adds products to the cart
        
            possible values of items:
            - a uid
            - list of uids (multiple products)
            - list of dicts with 'uid' and 'amount' key (multiple products with different amounts)
        """
        added = 0
        if isinstance(items, basestring):
            items = ({'uid': items,
                      'amount': int(amount)},)
        uids = getToolByName(self.context, 'uid_catalog').uniqueValuesFor('UID')
        for item in items:
            if isinstance(item, basestring):
                item = {'uid': item,
                        'amount': int(amount)}
            if item['uid'] in uids:
                added += self._addItem(item)
        return added
    
    def remove(self, items, amount=None):
        """ removes products from the cart
        
            possible values of items:
            - a uid
            - list of uids (multiple products)
            - list of dicts with 'uid' and 'amount' key (multiple products with different amounts)
        """
        removed = 0
        if isinstance(items, basestring):
            items = ({'uid': items,
                      'amount': amount},)
        for item in items:
            if isinstance(item, basestring):
                item = {'uid': item,
                        'amount': amount}
            if self.has_key(item['uid']):
                if not item['amount'] or int(item['amount']) is 0 or int(item['amount']) >= self[item['uid']]:
                    removed += self[item['uid']]
                    del self[item['uid']]
                else:
                    removed += int(item['amount'])
                    self[item['uid']] = self[item['uid']] - int(item['amount'])
        return removed
    
    def edit(self, items):
        """ edits the cart
        
            items has to be a list of dicts with keys 'uid', 'amount' and 'remove'
        """
        added = removed = 0
        uids = getToolByName(self.context, 'uid_catalog').uniqueValuesFor('UID')
        for item in items:
            if item.has_key('variation'):
                item['variation'].sort()
            if item['uid'] in uids and int(item['amount']) > 0 and (not item.has_key('remove') or not item['remove']):
                if item.has_key('variation') and item['variation']:
                    item = {'uid': tuple(item['variation']),
                            'amount': item['amount']}
                if self.has_key(item['uid']):
                    removed += self[item['uid']] > int(item['amount']) and self[item['uid']] - int(item['amount']) or 0
                    added += self[item['uid']] < int(item['amount']) and int(item['amount']) - self[item['uid']] or 0
                else:
                    added += int(item['amount'])
                self[item['uid']] = int(item['amount'])
            if (item.has_key('remove') and item['remove']) or int(item['amount']) is 0:
                uid = item.has_key('variation') and tuple(item['variation']) or item['uid']
                removed += self.remove([{'uid': uid,
                                         'amount': None}])
        return added, removed
    
    def clear(self):
        """ clears the cart
        """
        self._items = {}
        self._save()
    
    def _addItem(self, item):
        added = item['amount']
        if self.has_key(item['uid']):
            item['amount'] += self[item['uid']]
        self[item['uid']] = item['amount']
        return added
    
    def _save(self):
        self.context.REQUEST.SESSION.set(SESSION_KEY, self._items)

class OrderRegistry(Cart):
    """"""
    implements(IOrderRegistry)
    
    def __init__(self, context):
        self.context = context
        self.portal = getMultiAdapter((self.context, self.context.REQUEST), name=u'plone_portal_state').portal()
        annotations = IAnnotations(self.portal)
        self._items = annotations.get(ANNOTATIONS_KEY_ORDERS, PersistentDict())
        
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
    
    def create(self, order, zone=None):
        """ generates an order from the cart
        """
        member = getMultiAdapter((self.context, self.context.REQUEST), name=u'plone_portal_state').member()
        cart = IShoppingCart(self.context)
        taxes = ITaxes(self.context)
        if not len(cart):
            return
        order.userid = member.getId()
        order.zone = ('', 0)
        if zone and taxes.has_key(zone):
            order.zone = (zone, taxes[zone])
        order.date = time()
        order.products = []
        order.currency = CurrencyAware(0).getCurrencySymbol()
        products = cart.getProducts()
        price = 0
        for product in products:
            price += product['price_raw'] * product['amount']
            order.products.append((product['uid'],
                                   product['no'],
                                   product['title'],
                                   product['amount'],
                                   product['price_raw'],
                                   [(variation['uid'], variation['type'], variation['name']) for variation in product['variations']]))
        order.price = price
        self[order.orderid] = order
        
    def recover(self, orderid):
        """ recover an order from the registry
        """
        if not self.has_key(orderid):
            return
        order = self[orderid]
        cart = IShoppingCart(self.context)
        cart.clear()
        for uid, title, price_raw, amount, variations in order.products:
            if variations:
                cart.addVariation([uid for uid, type, name in variations], amount)
            else:
                cart.add(uid, amount)
                
    def send(self, orderid):
        """ sends an order
        """
        if not self.has_key(orderid):
            return
        order = self[orderid]
        if order.state is SENT:
            return
        request = self.context.REQUEST
        portal_state = getMultiAdapter((self.context, request), name=u'plone_portal_state')
        address = order.delivery
        products = []
        for product in order.products:
            products.append("%s\t\t\t\t%s\t%s\t\t%s" % (product[1], 
                                                        product[3], 
                                                        CurrencyAware(product[4]).valueToString(order.currency), 
                                                        CurrencyAware(product[4] * product[3]).valueToString(order.currency)))
            products.append(product[2].decode('utf-8'))
            for variation in product[5]:
                products.append("\t%s: %s" % (variation[1].decode('utf-8'), variation[2].decode('utf-8')))
            products.append("")
        
        msg = translate(_('email_order_body', default=\
"""
New order by ${name}

Orderid: ${orderid}

Order:

Product\t\t\t\tAmount\tPrice\t\tPrice total
-------------------------------------------------------------------

${products}
-------------------------------------------------------------------

Total:\t\t\t\t\t\t\t${price}
VAT:\t\t\t\t\t\t\t${tax}
Total incl. VAT:\t\t\t\t\t${total}

Currency: ${currency}


Delivery address:
Name: ${name}
Address 1: ${address1}
Address 2: ${address2}
ZIP: ${zip}
City: ${city}
Country: ${country}
Zone: ${zone}

Phone: ${phone}
eMail: ${email}
""", mapping={'orderid': order.orderid,
              'products': "\n".join(products),
              'price': CurrencyAware(order.price).valueToString(order.currency),
              'tax': '%s (%s %% - %s)' % (CurrencyAware(order.price_tax).valueToString(order.currency), order.tax, address.zone),
              'total': CurrencyAware(order.total).valueToString(order.currency),
              'currency': order.currency,
              'name': address.name,
              'address1': address.address1,
              'address2': address.address2,
              'zip': address.zip,
              'city': address.city,
              'country': address.country,
              'zone': address.zone,
              'phone': address.phone,
              'email': address.email}), context=request)
        mailhost = getToolByName(self.context, 'MailHost')
        mailhost.secureSend(msg,
                            mto=portal_state.portal().getProperty('email_from_address', ''),
                            mfrom='%s <%s>' % (address.name, address.email),
                            subject=translate(_('email_order_title', default='New order [${orderid}]', mapping={'orderid': order.orderid}), context=request),
                            charset='utf-8')
        order.state = SENT
    
    def _save(self):
        annotations = IAnnotations(self.portal)
        annotations[ANNOTATIONS_KEY_ORDERS] = self._items

class PaymentProcessor(object):
    """"""
    implements(IPaymentProcessor)

    def __init__(self, context):
        self.context = context
        
    def processPayment(self, view, method):
        registry = IOrderRegistry(self.context)
        self.order = registry.getOrder(view.getOrderId())
        if not self.order:
            return 'no matching order found'
        if self.order.state is not PROCESSED:
            if method.verifyPayment(self.context, self.order):
                self.order.state = PROCESSED
                notify(OrderProcessedEvent(self.order))
                return 'payment successfully processed'
            else:
                self.order.state = FAILED
                notify(OrderProcessingFailedEvent(self.order))
                return 'processing payment failed'
        return 'payment already processed'

class Imaging(object):
    """ An adapter to handle the images of a product
    """ 
    implements(IImaging)
    adapts(IProduct)
    
    def __init__(self, context):
        self.context = context
    
    def getImages(self):
        """ All image inside of the product
        """
        catalog = getToolByName(self.context, 'portal_catalog')
        images = catalog(object_provides=IImageContent.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()),
                                                                             'depth': 1})
        return images
        
class Pricing(object):
    """ An adapter to handle prices of a product
    """
    implements(IPricing)
    adapts(IProduct)
    
    def __init__(self, context):
        self.context = context
    
    def getPrice(self):
        """ The lowest available price
        """
        catalog = getToolByName(self.context, 'portal_catalog')
        prices = [float(p.getPrice) for p in catalog(object_provides=IPrice.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()),
                                                                                                  'depth': 1})]
        if float(self.context.getPrice()) > 0 and not (IVariation.providedBy(self.context) and self.context.getAddPrice()):
            prices.append(float(self.context.getPrice()))
        if IVariation.providedBy(self.context):
            prices.append(IPricing(aq_parent(self.context)).getPrice())
        
        return float(min(prices))
    
    def getBasePrice(self):
        """ The base price defined on the product
        """
        return float(self.context.getPrice())
        
class Taxes(object):
    """ An adapter to handle taxes based on zones
        
        len(Taxes)
        Taxes.has_key(key)
        Taxes.items()
        Taxes[key]
        Taxes[key] = value
        del(Taxes[key])
    """
    implements(ITaxes)
    
    _items = {}
    
    def __init__(self, context):
        self.context = context
        self.portal = getMultiAdapter((self.context, self.context.REQUEST), name=u'plone_portal_state').portal()
        annotations = IAnnotations(self.portal)
        self._items = dict(annotations.get(ANNOTATIONS_KEY_TAXES, ()))
    
    def __len__(self):
        return len(self._items)
    
    def __getitem__(self, key):
        return float(self._items[key])
    
    def __setitem__(self, key, value):
        if not isinstance(value, float):
            raise AttributeError, 'value has to be a float got %s' % type(value)
        self._items[key] = value
        self._save()
    
    def __delitem__(self, key):
        del(self._items[key])
        self._save()
    
    def has_key(self, key):
        return self._items.has_key(key)
    
    def items(self):
        return self._items.items()
        
    def edit(self, taxes):
        """ edits the taxes
        
            taxes has to be a list of dicts with keys 'zone', 'tax'
        """
        self._items = {}
        self._save()
        for tax in taxes:
            self[tax['zone']] = tax['tax']
    
    def _save(self):
        annotations = IAnnotations(self.portal)
        annotations[ANNOTATIONS_KEY_TAXES] = self.items()
