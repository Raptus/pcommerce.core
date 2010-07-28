from AccessControl import ModuleSecurityInfo
from Products.CMFCore.permissions import setDefaultRoles

security = ModuleSecurityInfo('pcommerce.core.config')

security.declarePublic('AddProduct')
AddProduct = 'PCommerce: Add Product'
setDefaultRoles(AddProduct, ('Manager','Contributer','Owner',))

security.declarePublic('AddVariation')
AddVariation = 'PCommerce: Add Variation'
setDefaultRoles(AddVariation, ('Manager','Contributer','Owner',))

security.declarePublic('AddImage')
AddVariation = 'PCommerce: Add Image'
setDefaultRoles(AddVariation, ('Manager','Contributer','Owner',))

security.declarePublic('AddPrice')
AddPrice = 'PCommerce: Add Price'
setDefaultRoles(AddPrice, ('Manager','Contributer','Owner',))

security.declarePublic('AddToCart')
AddToCart = 'PCommerce: Add to Cart'
setDefaultRoles(AddToCart, ('Anonymous', 'Authenticated',))

security.declarePublic('CheckOut')
CheckOut = 'PCommerce: Check out'
setDefaultRoles(CheckOut, ('Authenticated',))

security.declarePublic('ManageOrders')
ManageOrders = 'PCommerce: Manage Orders'
setDefaultRoles(ManageOrders, ('Manager',))

permissions = {'Product': AddProduct,
               'Variation': AddVariation,
               'Price': AddPrice}

INITIALIZED = 1
SENT = 2
PROCESSED = 3
FAILED = 4
CANCELED = 5

PROJECTNAME = "pcommerce.core"

product_globals = globals()