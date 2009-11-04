from zope.interface import Interface, Attribute

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
        """ returns list of products currently in the cart
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
    
    def createFromSession(zone, info={}):
        """ generates an order from the cart
        """
        
    def recoverOrder(orderid):
        """ recover an order from the registry
        """
                
    def sendOrder(orderid):
        """ sends an order
        """
        
class IAddress(Interface):
    """"""
    
    name = Attribute("""string""")
    
    address1 = Attribute("""string""")
    
    address2 = Attribute("""string""")
    
    zip = Attribute("""string""")
    
    city = Attribute("""string""")
    
    country = Attribute("""string""")
    
    zone = Attribute("""string""")
    
    email = Attribute("""string""")
    
    phone = Attribute("""string""")
        
class IOrder(Interface):
    """"""
    
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
        """tuple: (name, tax)""")
    
    delivery = Attribute(
        """address""")
    
    currency = Attribute(
        """string: the currency""")

class IOrderEvent(Interface):
    """An event that's fired upon order change.
    """
    order = Attribute(u'The order object')
    
class IOrderProcessedEvent(IOrderEvent):
    """An event fired after a order has been processed
    """
    
class IOrderProcessingFailedEvent(IOrderEvent):
    """An event that's fired if processiong an order failed
    """

class IPaymentProcessor(Interface):
    """
    """
        
class IProcessView(Interface):
    """A view to process a payment of a specific payment-method"""
    
    def getOrderId(self):
        """returns the orderid"""

class IPaymentRegistry(Interface):
    """A utility holding registered payment-utilities"""

    def getPaymentMethods():
        """get all registered payment-methods"""

class IPaymentMethod(Interface):
    """A payment-method"""

    title = Attribute(
        """unicode: the title of the payment method""")

    decription = Attribute(
        """unicode: the description of the payment method""")

    icon = Attribute(
        """string: icon resource""")

    logo = Attribute(
        """string: logo resource""")

    pre_view_name = Attribute(
        """string: the name of the view used pre order""")

    info_view_name = Attribute(
        """string: the name of the view used to display additional informations""")

    post_view_name = Attribute(
        """string: the name of the view used post order""")
    
    def convertAmount(amount):
        """method to convert the amount"""

    def getOrderId(context):
        """returns the unique id of an order"""
    
    def getOrder(context):
        """returns an object implementing the IOrder-interface"""

    def startCheckout(context):
        """start the payment process"""
        
    def checkout(context, order):
        """"""

    def cancelCheckout(context, order):
        """cancel the payment process"""

    def verifyPayment(context, order):
        """checks whether the payment was successfull or not"""
        
class IPostOrderFormView(Interface):
    """Marker interface for payment-forms which are view-classes rather than simple page-templates"""
    
class IPreOrderView(Interface):
    """"""
    
    def validate(order):
        """"""
        
    def process(order):
        """"""
    
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
        
            taxes has to be a list of dicts with keys 'zone', 'tax'
        """
        