from DateTime import DateTime

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.interfaces import IOrderRegistry

class ManageOrders(BrowserView):
    """Overview of all orders.
    """

    template = ViewPageTemplateFile('manage_orders.pt')

    def __init__(self, *args, **kwargs):
        super(ManageOrders, self).__init__(*args, **kwargs)
        self.translation_service = getToolByName(self.context, 
            'translation_service')
        self.registry = IOrderRegistry(self.context)

    def __call__(self):
        self.request.set('disable_border', 1)
        return self.template()

    def _translate_order_status_id(self, status_id):
        """
        """
        order_status_string = {
            1: _('label_initialized', default="Initialized"),
            2: _('label_sent', default="Sent"),
            3: _('label_processed', default="Processed"),
            4: _('label_failed', default="Failed"),
            5: _('label_cancelled', default="Cancelled"),
        }
        return order_status_string[status_id]

    def _order_fields(self):
        """Fields and fieldnames to show in tables (order overviews / details).

            {   'field_id': '', 
                'field_name': _("label_", default=""),
                },
        """
        fields = [
            {   'field_id': 'orderid', 
                'field_name': _("label_order_id", default="Order id"),
                },
            {   'field_id': 'userid', 
                'field_name': _("label_user_id", default="User id"),
                },
            {   'field_id': 'date', 
                'field_name': _("label_date", default="Date"),
                },
            {   'field_id': 'currency', 
                'field_name': _("label_currency", default="Currency"),
                },
            {   'field_id': 'price', 
                'field_name': _("label_price_total", default="Price total"),
                },
            {   'field_id': 'state', 
                'field_name': _("label_order_state", default="Order status"),
                },
            {   'field_id': 'zone', 
                'field_name': _("label_zone", default="Zone"),
                },
            {   'field_id': 'address', 
                'field_name': _("label_address", default="Address"),
                },
            {   'field_id': 'products', 
                'field_name': _("label_products", default="Products"),
                },
            {   'field_id': 'shipmentids', 
                'field_name': _("label_shipmentids", default="Shipment id's"),
                },
            ]
        return fields

    def _order_management_columns(self):
        """Fields for order management table. """
        field_ids = [
            'orderid',
            'userid',
            'date',
            'currency',
            'price',
            'state',
            ]
        columns = [ column for column in self._order_fields() if \
            column['field_id'] in field_ids]
        return columns

    def _massageData(self, field_id, value):
        """Modify the field values (if needed) for displaying to humans. """
        # Convert the date (float) to a DateTime format.
        if field_id == 'date':
            value = DateTime(value)
            value = self.translation_service.ulocalized_time(
                value, long_format=True, time_only=None, 
                context=self.context, domain='plonelocales', 
                request=self.request)
        # Convert order status to a translated string
        if field_id == 'state':
            value = self._translate_order_status_id(value)
        return value

    def _get_order_data(self, order_nr, fields):
        """Returns data of a single order as as a list of dictionaries, 
        suitable for displaying in a page template.

        Copies only the specified fields (which are defined like the 
        _order_fields list of dicts above.

        [   {   'id':   ..., # field id
                'value: ..., # field value
                'name': ..., # field name (optional)
            },
        ]
        """
        r_order = self.registry.getOrder(order_nr)
        order_data = []
        for field in fields:
            field_data = {}
            field_id = field['field_id']
            field_data['id'] = field_id
            value = getattr(r_order, field_id)
            field_data['value'] = self._massageData(field_id, value)
            field_data['name'] = field['field_name']
            order_data.append(field_data)
        return order_data

    def orders(self):
        """Returns data rows for order management table. """
        orders = []
        # use only selected fields in the table
        columns = self._order_management_columns()
        for order_nr in self.registry.getOrders():
            orders.append(self._get_order_data(order_nr, columns))
        return orders

class OrderDetails(ManageOrders):
    """View order details. 

    Subclassed from ManageOrders for easy code reuse.
    """
    template = ViewPageTemplateFile('order_details.pt')

    def __call__(self):
        self.request.set('disable_border', 1)
        self.order_id = int(self.request.get('order_id'))

        # use all fields
        fields = self._order_fields()

        self.order = self._get_order_data(
            self.order_id,
            fields,
            )
        return self.template()
