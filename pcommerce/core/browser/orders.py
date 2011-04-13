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
        """
        """
        super(ManageOrders, self).__init__(*args, **kwargs)
        self.translation_service = getToolByName(self.context, 
            'translation_service')
        self.registry = IOrderRegistry(self.context)

    def __call__(self):
        self.request.set('disable_border', 1)
        return self.template()

    def _columns(self):
        """Define columns for order management table. 

            {   'field_id': '', 
                'field_name': _("label_", default=""),
                },
        """
        columns = [
            {   'field_id': 'orderid', 
                'field_name': _("label_order_id", default="Order id"),
                },
            {   'field_id': 'userid', 
                'field_name': _("label_user_id", default="User id"),
                },
            {   'field_id': 'date', 
                'field_name': _("label_date", default="Date"),
                },
            {   'field_id': 'price', 
                'field_name': _("label_price_total", default="Price total"),
                },
            {   'field_id': 'state', 
                'field_name': _("label_order_state", default="Order status"),
                },
            ]
        return columns

    def column_names(self):
        """Return list of translated column names for order management table.
        """
        return [field['field_name'] for field in self._columns()]

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

    def orders(self):
        """Returns data rows for order management table. """
        orders = []
        for order_nr in self.registry.getOrders():
            r_order = self.registry.getOrder(order_nr)
            order = {'data': []}
            for column in self._columns():
                field_id = column['field_id']
                value = getattr(r_order, field_id)
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
                order['data'].append(value)
            orders.append(order)
        return orders
