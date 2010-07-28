from zope.interface import Interface, Attribute
from zope.publisher.interfaces.browser import IBrowserView

class IProduct(Interface):
    """ A product
    """

class IVariation(IProduct):
    """ A variation of a product
    """
    
class IShop(Interface):
    """ shop view
    """
    
class IShopFolder(Interface):
    """ shop folder view
    """

class IPrice(Interface):
    """ A price
    """
    
class IShoppingCart(Interface):
    """ An adapter to handle a shopping cart
    
        the adapter supports the following stanard python methods:
        
        len(ShoppingCart)
        ShoppingCart.has_key(key)
        ShoppingCart.items()
        ShoppingCart[key]
        ShoppingCart[key] = value
        del ShoppingCart[key]
    """
    
    def getProducts():
        """ returns a list of products currently in the cart
        """
    
    def getPrice():
        """ returns the total price of all products in the cart
        """
        
    def addVariation(item, amount=1):
        """ adds a variation of a product to the cart
        
            possible values of item:
            - a uid
            - a list of uids (combination of  multiple variations)
        """
        
    def add(items, amount=1):
        """ adds products to the cart
        
            possible values of items:
            - a uid
            - list of uids (multiple products)
            - list of dicts with 'uid' and 'amount' key (multiple products with different amounts)
        """
        
    def remove(items, amount=None):
        """ removes products from the cart
        
            possible values of items:
            - a uid
            - list of uids (multiple products)
            - list of dicts with 'uid' and 'amount' key (multiple products with different amounts)
        """
            
    def edit(items):
        """ edits the cart
        
            items has to be a list of dicts with keys 'uid', 'amount' and 'remove'
        """
        
    def clear():
        """ clears the cart
        """
    
class IOrderRegistry(Interface):
    """ An adapter to handle the order registry
    
        the adapter supports the following standard python methods:
        
        len(OrderRegistry)
        OrderRegistry.has_key(key)
        OrderRegistry.items()
        OrderRegistry[key]
        OrderRegistry[key] = value
    """
    
    def getOrders():
        """ returns a list of orders
        """
    
    def getOrder(orderid):
        """ returns a order by its id
        """
    
    def create(order):
        """ generates an order from the cart
        """
        
    def recover(orderid):
        """ recover an order from the registry
        """
                
    def send(orderid, lang=None):
        """ sends an order
        """
        
    def cancel(orderid):
        """ cancel an order
        """
        
    def fail(orderid):
        """ fail an order
        """
        
class IAddress(Interface):
    """ An address
    """
    
    salutation = Attribute("""string""")
    
    name = Attribute("""string""")
    
    address1 = Attribute("""string""")
    
    address2 = Attribute("""string""")
    
    zip = Attribute("""string""")
    
    city = Attribute("""string""")
    
    country = Attribute("""string""")
    
    zone = Attribute("""string""")
    
    email = Attribute("""string""")
    
    phone = Attribute("""string""")
    
    def mailInfo(request, lang=None, customer=False):
        """ returns plain text information about the address to be sent by email """
    
class IAddressFactory(Interface):
    """ An adapter to validate and create IAddress objects
    """
    
    def create(tag):
        """ Returns a new Address object based on the request
        """
        
    def validate(tag):
        """ Validates the data in the request to match the ones used for an Address
        """
        
class IOrder(Interface):
    """ An order
    """
    
    state = Attribute(
        """integer: the current state of the order""")
    
    orderid = Attribute(
        """string: the orderid""")
    
    userid = Attribute(
        """string: the userid""")
    
    products = Attribute(
        """list: list of products""")
    
    date = Attribute(
        """time""")
    
    price = Attribute(
        """float: the price""")
    
    zone = Attribute(
        """tuple: (name, (tax, taxname))""")
    
    currency = Attribute(
        """string: the currency""")
    
    address = Attribute(
        """IAddress: customer address""")
    
    paymentid = Attribute(
        """string: name of the payment method""")
    
    paymentdata = Attribute(
        """IPayment: data stored by the payment method""")
    
    shipmentids = Attribute(
        """dict: mapping of shipmentid to product uids""")
    
    shipmentdata = Attribute(
        """dict: mapping of IShipmentData objects to shipmentid""")
    
    pretaxcharges = Attribute(
        """tuple: list of IChargeData objects""")
    
    posttaxcharges = Attribute(
        """tuple: list of IChargeData objects""")
    
    total = Attribute(
        """float: the total price including tax and pre tax shipment prices""")
    
    subtotal = Attribute(
        """float: the total price including pre tax shipment prices""")
    
    totalincl = Attribute(
        """float: the total price including tax and shipment prices""")
    
    pretaxcharge = Attribute(
        """float: pre tax charge""")
    
    posttaxcharge = Attribute(
        """float: post tax charge""")
    
    zonename = Attribute(
        """string: the name of the zone""")
    
    taxname = Attribute(
        """string: the name of the tax""")
    
    tax = Attribute(
        """float: the tax factor""")
    
    pricetax = Attribute(
        """float: the tax price""")
        
class IPaymentProcessor(Interface):
    """"""
    
    def processOrder(orderid, paymentid, lang=None):
        """ Processes an order """
    
class IOrderEvent(Interface):
    """ An event that's fired upon order change.
    """
    order = Attribute(u'The order object')
    
class IOrderProcessedEvent(IOrderEvent):
    """ An event fired after a order has been processed
    """
    
class IOrderProcessingFailedEvent(IOrderEvent):
    """ An event that's fired if processiong an order failed
    """
    
class IPricing(Interface):
    """ An adapter to handle prices of a product
    """
    
    def getPrice():
        """ The lowest available price
        """
        
    def getBasePrice():
        """ The base price defined on the product
        """
        
class IImaging(Interface):
    """ An adapter to handle images of a product
    """
    
    def getImages():
        """ All Images inside of the Product
        """
        
class ITaxes(Interface):
    """ An adapter to handle taxes based on zones
        
        len(Taxes)
        Taxes.has_key(key)
        Taxes.items()
        Taxes[key]
        Taxes[key] = value
        del Taxes[key]
    """
        
    def edit(taxes):
        """ edits the taxes
        
            taxes has to be a list of dicts with keys 'zone', 'tax', 'taxname'
        """

class ICheckoutView(Interface):
    """ Checkout view
    """

class ISteps(Interface):
    """ Steps provider
    """
    
class IComponent(IBrowserView):
    """ A component for the checkout steps
    """
    
    dependencies  = Attribute(u'Tuple: name of dependencies components')
    
    def validate(self):
        """ validate the form values """

    def process(self):
        """ process of the component """
    
    def renders(self):
        """ defines whether a component renders or not """

class IPaymentRegistry(Interface):
    """ An adapter holding registered payment
    """

    def getPayments():
        """ get all registered payment methods """
        
class IShipmentRegistry(Interface):
    """ An adapter holding registered shipments
    """

    def getShipments():
        """ get all registered shipment methods """
        
class IPaymentMethod(Interface):
    """ A payment method
    """

    title = Attribute(
        """unicode: the title of the payment method""")

    decription = Attribute(
        """unicode: the description of the payment method""")

    icon = Attribute(
        """string: icon resource""")

    logo = Attribute(
        """string: logo resource""")
    
    def verifyPayment(order):
        """verify the payment"""
    
    def mailInfo(order, lang=None, customer=False):
        """ returns plain text information about the payment to be sent by email """
    
class IPaymentData(Interface):
    """ A payment object to be stored on the order
    """
    
    paymentid = Attribute(
        """ the name of the corresponding payment method """)
        
    pretaxcharge = Attribute(
        """ returns the pre tax charge for this payment """)
        
    posttaxcharge = Attribute(
        """ returns the post tax charge for this payment """)

class IPaymentView(Interface):
    """ A payment view
    """
    
    def validate(self):
        """ validate the form values """

    def process(self):
        """ process of the payment view and return a IPaymentData object """
    
    def renders(self):
        """ defines whether a payment view renders or not """
    
class IShipmentMethod(Interface):
    """ A shipment method
    """

    title = Attribute(
        """unicode: the title of the payment method""")

    decription = Attribute(
        """unicode: the description of the payment method""")

    icon = Attribute(
        """string: icon resource""")

    logo = Attribute(
        """string: logo resource""")
    
    def mailInfo(order, lang=None, customer=False):
        """ returns plain text information about the shipment to be sent by email """
    
class IShipmentData(Interface):
    """ A shipment object to be stored on the order
    """
    
    shipmentid = Attribute(
        """ the name of the corresponding shipment method """)
        
    pretaxcharge = Attribute(
        """ returns the pre tax charge for this shipment """)
        
    posttaxcharge = Attribute(
        """ returns the post tax charge for this shipment """)

class IShipmentView(Interface):
    """ A shipment view
    """
    
    def validate(self):
        """ validate the form values """

    def process(self):
        """ process of the shipment view and return a IShipmentData object """

    def renders(self):
        """ defines whether a shipment view renders or not """
        
class IPreTaxCharge(Interface):
    """ An adapter to provide a pre tax charge
    """
    
    def process(order):
        """ returns an IChargeData object containing the charge """
        
class IPostTaxCharge(Interface):
    """ An adapter to provide a post tax charge
    """
    
    def process(order):
        """ returns an IChargeData object containing the charge """
        
class IChargeData(Interface):
    """ An additional charge for an order
    """
    
    title = Attribute(
        """unicode: the title of the charge""")
    
    price = Attribute(
        """flaot: the price""")
