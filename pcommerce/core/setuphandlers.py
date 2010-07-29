from pcommerce.core.interfaces import IOrderRegistry

def migrate05a105a2(context):

    if context.readDataFile('pcommerce.core_migrate05a105a2.txt') is None:
        return
    
    portal = context.getSite()
    
    registry = IOrderRegistry(portal)
    for order in registry.getOrders().itervalues():
        if hasattr(order.paymentdata, 'shipmentid'):
            order.paymentdata.id = order.paymentdata.shipmentid
            delattr(order.paymentdata, 'shipmentid')
        for data in order.shipmentdata.values():
            if hasattr(data, 'shipmentid'):
                data.id = data.shipmentid
                delattr(data, 'shipmentid')
    