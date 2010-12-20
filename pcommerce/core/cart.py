from zope.interface import implements, Interface
from zope.component import adapts

from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName

from pcommerce.core.currency import CurrencyAware
from pcommerce.core import interfaces

SESSION_KEY = 'pcommerce.core.cart'

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
    
        the adapter supports the following standard python methods:
        
        len(ShoppingCart)
        ShoppingCart.has_key(key)
        ShoppingCart.items()
        ShoppingCart[key]
        ShoppingCart[key] = value
        del(ShoppingCart[key])
    """
    implements(interfaces.IShoppingCart)
    adapts(Interface)
    
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
        price = 0.0
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
            results = [product.getObject() for product in catalog(object_provides=interfaces.IProduct.__identifier__, UID=uid)]
            if results:
                price = 0
                add_price = 0
                variations = []
                variations_raw = []
                product = None
                for result in results:
                    if interfaces.IVariation.providedBy(result):
                        variations_raw.append(result)
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
                        variations.append(variation)
                        if not product:
                            product = aq_parent(result)
                    else:
                        product = result
                
                price = interfaces.IPricing(product).getPrice(variations_raw)
                products.append({'title': product.Title(),
                                 'no': product.getNo(),
                                 'description': product.Description(),
                                 'price': CurrencyAware(price),
                                 'price_raw': price,
                                 'price_total': CurrencyAware(price * amount),
                                 'price_total_raw': price * amount,
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
