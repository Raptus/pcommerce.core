from zope.interface import implements, Interface
from zope.component import adapts, getMultiAdapter, queryMultiAdapter, getAdapter

from plone.memoize.instance import memoize

from Products.Five.browser import BrowserView

from pcommerce.core import interfaces
from pcommerce.core.currency import CurrencyAware

class BaseComponent(BrowserView):
    implements(interfaces.IComponent)
    adapts(Interface)
    
    errors = {}
    cart = None
    order = None
    dependencies = ()
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.order = interfaces.IOrder(self.context)
        self.cart = interfaces.IShoppingCart(self.context)
        
    def __call__(self):
        return self.template()

    def _shipments(self):
        registry = interfaces.IShipmentRegistry(self.context)
        return registry.getShipmentMethods()
    
    def _shipmentgroups(self):
        groups = {}
        products = self.products
        for product in products:
            product = product['object']
            shipmentids = product.getShipments()
            shipmentids = list(shipmentids)
            shipmentids.sort()
            shipmentids = tuple(shipmentids)
            if groups.has_key(shipmentids):
                groups[shipmentids].append(product)
            else:
                groups[shipmentids] = [product,]
        return groups
    
    @property
    def shipmentgroups(self):
        group = []
        shipmentgroups = self._shipmentgroups()
        shipments = self._shipments()
        for shipmentids, products in shipmentgroups.items():
            mapping = []
            for id in shipmentids:
                if shipments.has_key(id):
                    shipment = shipments[id]
                    
                    # check is selected
                    selected = False                  
                    uids = []
                    for product in products:
                        uids.append(product.UID())
                    uids = tuple(uids)
                    for shipment_id, products_uids in self.context.order.shipmentids.items():
                        if shipment_id == id and products_uids == uids:
                            selected = True
                            break
                    
                    mapping.append({'id': id,
                                    'title': shipment.title,
                                    'description': shipment.description,
                                    'icon': shipment.icon,
                                    'logo': shipment.logo,
                                    'selected': selected})
            group.append({'shipments': mapping,
                          'products': products,
                          'shipmentids': shipmentids, })
        return group
    
    @property
    @memoize
    def shipments(self):
        shipments =[]
        i = 1
        for shipmentid, products in self.order.shipmentids.items():
            shipment = getAdapter(self.context, name=shipmentid, interface=interfaces.IShipmentMethod)
            data = {'id': shipmentid,
                    'plugin': shipment,
                    'title': shipment.title,
                    'description': shipment.description,
                    'icon': shipment.icon,
                    'logo': shipment.logo,
                    'products': products,
                    'renders': False,
                    'view': None,
                    'number': i}
            shipmentview = queryMultiAdapter((shipment, self.request), name=self.__name__, interface=interfaces.IShipmentView)
            if shipmentview is not None:
                data['view'] = shipmentview.__of__(self.context)
                data['renders'] = data['view'].renders()
            shipments.append(data)
            i += 1
        return shipments
    
    def _payments(self):
        registry = interfaces.IPaymentRegistry(self.context)
        return registry.getPaymentMethods()
    
    @property
    def payments(self):
        payments = []
        for name, payment in self._payments().items():
            selected = False
            if name == self.context.order.paymentid:
                selected = True
            payments.append({'id': name,
                             'plugin': payment,
                             'title': payment.title,
                             'description': payment.description,
                             'icon': payment.icon,
                             'logo': payment.logo,
                             'selected': selected})
        return payments
    
    @property
    def payment(self):
        payment = self._payments().get(self.order.paymentid, None)
        if payment is None:
            return None
        data = {'id': self.order.paymentid,
                'plugin': payment,
                'title': payment.title,
                'description': payment.description,
                'icon': payment.icon,
                'logo': payment.logo,
                'view': None}
        view = queryMultiAdapter((payment, self.request), name=self.__name__, interface=interfaces.IPaymentView)
        if view is not None:
            data['view'] = view.__of__(self.context)
        return data
    
    @property
    @memoize
    def paymentview(self):
        return self.payment and self.payment['view'] or None
    
    def action(self):
        if self.paymentview is not None:
            if hasattr(self.paymentview, 'action'):
                return self.paymentview.action()
        return None
    
    @property
    def products(self):
        return self.cart.getProducts()
    
    def getProductNumber(self, uid):
        if len(self.shipments) == 1:
            return None
        for shipment in self.shipments:
            if uid in shipment['products']:
                return shipment['number']
        return None
    
    @property
    def price(self):
        if self.order:
            return CurrencyAware(self.order.price)
        return CurrencyAware(self.cart.getPrice())
    
    @property
    def pricetax(self):
        if self.order:
            return CurrencyAware(self.order.pricetax)
        return None
    
    @property
    def pricetaxincl(self):
        if self.order:
            return CurrencyAware(self.order.pricetaxincl)
        return None
    
    @property
    def pretaxcharges(self):
        charges = []
        if getattr(self.order.paymentdata, 'pretaxcharge', 0):
            charges.append({'title': self.payment['title'],
                            'price': CurrencyAware(getattr(self.order.paymentdata, 'pretaxcharge', 0))})
        for shipmentid, data in self.order.shipmentdata.items():
            if not data.pretaxcharge:
                continue
            for shipment in self.shipments:
                if shipmentid == shipment['id']:
                    charges.append({'title': shipment['title'],
                                    'number': len(self.shipments) > 1 and shipment['number'] or None,
                                    'price': CurrencyAware(data.pretaxcharge)})
        for charge in self.order.pretaxcharges:
            if charge.price:
                charges.append({'title': charge.title,
                                'price': CurrencyAware(charge.price)})
        return charges
    
    @property
    def subtotal(self):
        if self.order.pretaxcharge:
            return CurrencyAware(self.order.subtotal)
        return None
    
    @property
    def posttaxcharges(self):
        charges = []
        if getattr(self.order.paymentdata, 'posttaxcharge', 0):
            charges.append({'title': self.payment['title'],
                            'price': CurrencyAware(getattr(self.order.paymentdata, 'posttaxcharge', 0))})
        for shipmentid, data in self.order.shipmentdata.items():
            if not data.posttaxcharge:
                continue
            for shipment in self.shipments:
                if shipmentid == shipment['id']:
                    charges.append({'title': shipment['title'],
                                    'number': len(self.shipments) > 1 and shipment['number'] or None,
                                    'price': CurrencyAware(data.posttaxcharge)})
        for charge in self.order.posttaxcharges:
            if charge.price:
                charges.append({'title': charge.title,
                                'price': CurrencyAware(charge.price)})
        return charges
    
    @property
    def totalincl(self):
        if self.order.posttaxcharge:
            return CurrencyAware(self.order.totalincl)
        return None
    
    @property
    def taxincl(self):
        if self.order:
            return self.order.taxincl
        return None
    
    @property
    def taxinclname(self):
        if self.order:
            return self.order.taxinclname
        return None
    
    @property
    def tax(self):
        if self.order:
            return self.order.tax
        return None
    
    @property
    def taxname(self):
        if self.order:
            return self.order.taxname
        return None
    
    @property
    def total(self):
        if self.order:
            return CurrencyAware(self.order.total)
        return None
    
    @property
    def zones(self):
        taxes = interfaces.ITaxes(self.context)
        return taxes.keys()
    
    def renders(self):
        return True
