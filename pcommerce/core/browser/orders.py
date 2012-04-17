import os

from DateTime import DateTime

from zope.i18n import translate

from plone.app.content.batching import Batch
from plone.app.content.browser import tableview

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.currency import CurrencyAware
from pcommerce.core import PCommerceMessageFactory as _
from pcommerce.core.interfaces import IOrderRegistry


SESSION_KEY = 'pcommerce.core.manageorders.'

class ManageOrders(BrowserView):
    """Overview of all orders.
    """

    template = ViewPageTemplateFile('manage_orders.pt')
    batching = ViewPageTemplateFile(os.path.join(os.path.dirname(tableview.__file__), 'batching.pt'))

    def __init__(self, *args, **kwargs):
        super(ManageOrders, self).__init__(*args, **kwargs)
        self.translation_service = getToolByName(self.context, 
            'translation_service')
        self.registry = IOrderRegistry(self.context)
        self.pagesize = 20
        session = self.request.SESSION
        self.pagenumber = session.get(SESSION_KEY + 'pagenumber', 1)
        if self.request.get('pagenumber', None) is not None:
            self.pagenumber = int(self.request.get('pagenumber'))
            session.set(SESSION_KEY + 'pagenumber', self.pagenumber)
        self.sort_on = session.get(SESSION_KEY + 'sort_on', 1)
        self.reverse = session.get(SESSION_KEY + 'reverse', False)
        if not self.request.get('sort_on', None) in ('getObjPositionInParent', '', None):
            if self.request.get('sort_on', None) == self.sort_on:
                self.reverse = not self.reverse
            else:
                self.reverse = False
            self.sort_on = self.request.get('sort_on')
            session.set(SESSION_KEY + 'reverse', self.reverse)
            session.set(SESSION_KEY + 'sort_on', self.sort_on)
            self.request.set('sort_on', '')
        self.url = '%s/@@manage-orders' % self.context.absolute_url()

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

    def order_fields(self):
        """Fields and fieldnames to show in tables (order overviews / details).

            {   'field_id': '',
                'field_name': _("label_", default=""),
                'sortable': True
                },
        """
        fields = [
            {   'field_id': 'orderid',
                'field_name': _("label_order_id", default="Order id"),
                'sortable': True
                },
            {   'field_id': 'userid',
                'field_name': _("label_user_id", default="User id"),
                'sortable': True
                },
            {   'field_id': 'date',
                'field_name': _("label_date", default="Date"),
                'sortable': True
                },
            {   'field_id': 'currency',
                'field_name': _("label_currency", default="Currency"),
                'sortable': True
                },
            {   'field_id': 'totalincl',
                'field_name': _("label_price_total", default="Price total"),
                'field_converter': self._totalincl_converter,
                'sortable': True
                },
            {   'field_id': 'state',
                'field_name': _("label_order_state", default="Order status"),
                'sortable': True
                },
            {   'field_id': 'zone',
                'field_name': _("label_zone", default="Zone"),
                'field_converter': self._zone_converter,
                'sortable': True
                },
            {   'field_id': 'address',
                'field_name': _("label_address", default="Address"),
                'field_converter': self._address_converter,
                'sortable': True
                },
            {   'field_id': 'products',
                'field_name': _("label_products", default="Products"),
                'field_converter': self._products_converter,
                'sortable': False
                },
            {   'field_id': 'shipmentids',
                'field_name': _("label_shipmentids", default="Shipment id's"),
                'field_converter': self._shipmentids_converter,
                'sortable': False
                },
            ]
        return fields

    def _zone_converter(self, value, order):
        return '<strong>%s</strong> (%s%% %s)' % (value[0], value[1][0], value[1][1])

    def _totalincl_converter(self, value, order):
        return CurrencyAware(value).valueToString()

    def _address_converter(self, value, order):
        return '<pre>%s</pre>' % value.mailInfo(self.request)

    def _products_converter(self, value, order):
        rows = []
        for product in value:
            cells = [str(i) for i in product[1:5]]
            cells.append(str(product[3]*product[4]))
            rows.append('</td><td>'.join(cells))
        return '''
<table class="listing">
    <thead>
        <tr><th>%s</th></tr>
    </thead>
    <tbody>
        <tr><td>%s</td></tr>
    </tbody>
</table>''' % ('</th><th>'.join((translate(_(u'No'), context=self.request),
                                 translate(_(u'Product'), context=self.request),
                                 translate(_(u'Amount'), context=self.request),
                                 translate(_(u'Price'), context=self.request),
                                 translate(_(u'Price total'), context=self.request))), '</td></tr><tr><td>'.join(rows))

    def _shipmentids_converter(self, value, order):
        return '<ul><li>%s</li></ul>' % '</li><li>'.join(value.keys())

    def order_management_columns(self):
        """Fields for order management table. """
        field_ids = [
            'orderid',
            'userid',
            'date',
            'currency',
            'totalincl',
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
        sort = 0
        for field in fields:
            field_data = {}
            field_id = field['field_id']
            field_data['id'] = field_id
            value = getattr(r_order, field_id)
            if field_id == self.sort_on:
                sort = value
            if field.has_key('field_converter'):
                try:
                    value = field['field_converter'](value, r_order)
                except:
                    pass
            field_data['value'] = self._massageData(field_id, value)
            field_data['name'] = field['field_name']
            order_data.append(field_data)
        return order_data, sort

    @property
    def batch(self):
        """Returns data rows for order management table. """
        orders = []
        sorting = []
        # use only selected fields in the table
        columns = self.order_management_columns()
        for order_nr in self.registry.getOrders():
            data, sort = self._get_order_data(order_nr, columns)
            index = len(orders) - 1
            while index >= 0 and sort < sorting[index]:
                index -= 1
            sorting.insert(index + 1, sort)
            orders.insert(index + 1, data)
        if self.reverse:
            orders.reverse()
        pagesize = self.pagesize
        b = Batch(orders,
                  pagesize=pagesize,
                  pagenumber=self.pagenumber)
        return b

class OrderDetails(ManageOrders):
    """View order details. 

    Subclassed from ManageOrders for easy code reuse.
    """
    template = ViewPageTemplateFile('order_details.pt')

    def __call__(self):
        self.request.set('disable_border', 1)
        self.order_id = int(self.request.get('order_id'))

        # use all fields
        fields = self.order_fields()

        self.order, sort = self._get_order_data(
            self.order_id,
            fields,
            )
        return self.template()
