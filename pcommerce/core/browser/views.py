from Acquisition import aq_inner, aq_parent

from zope.component import getMultiAdapter
from zope.interface import implements

from Products.statusmessages.interfaces import IStatusMessage

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from plone.memoize.instance import memoize

from plone.app.content.browser.interfaces import IFolderContentsView
from plone.app.content.browser.foldercontents import FolderContentsView, FolderContentsTable
from plone.app.content import browser
from plone.app.content.batching import Batch
batching_path = '/'.join(browser.__path__)

from Products.CMFPlone import PloneMessageFactory as _p

from pcommerce.core.config import CheckOut
from pcommerce.core.interfaces import IProduct, IVariation, IPrice, IPricing, IImaging, IShoppingCart, ITaxes, IShopFolder, IShop
from Products.ATContentTypes.interface.image import IImageContent
from pcommerce.core.currency import CurrencyAware
from pcommerce.core import PCommerceMessageFactory as _

from Products.CMFCore.utils import getToolByName

class ShopHomeView(BrowserView):
    """ shop home view
    """
    implements(IShop)
    
    template = ViewPageTemplateFile('templates/folder.pt')

    def __call__(self):
        return self.template()

class ShopFolderListing(BrowserView):
    """ shop folder listing
    """
    implements(IShopFolder)

    template = ViewPageTemplateFile('templates/folder.pt')
    batching = ViewPageTemplateFile('%s/batching.pt' % batching_path)

    def __call__(self):
        self.page = int(self.request.get('pagenumber', 1))
        self.url = self.context.absolute_url()
        return self.template()

    @property
    @memoize
    def batch(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        columns = int(props.getProperty('columns', 3))
        width = int(props.getProperty('thumb_width', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        results = catalog(object_provides=IProduct.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()), 'depth': 1}, sort_on='getObjPositionInParent')
        items = []
        i = 0
        start = (self.page-1) * (columns * 5)
        end = start + columns * 5
        for item in results:
            if start <= i < end:
                object = item.getObject()
                col = i % columns + 1
                adapter = IPricing(object)
                image = None
                if object.getImage():
                    image = {'caption': object.getImageCaption(),
                             'thumb': '%s/%s' % (item.getURL(), width)}
                item = {'uid': item.UID,
                        'class': 'col%s' % col,
                        'title': item.Title,
                        'description': item.Description,
                        'price': CurrencyAware(adapter.getPrice()),
                        'base_price': CurrencyAware(adapter.getBasePrice()),
                        'offer': adapter.getPrice() < adapter.getBasePrice(),
                        'image': image,
                        'url': item.getURL()}
            else:
                item = {'uid': item.UID,
                        'title': item.Title,
                        'description': item.Description,
                        'url': item.getURL()}
            i += 1
            items.append(item)
        return Batch(items, columns * 5, self.page, 5)
        
    @property
    @memoize
    def multiple_pages(self):
        return self.batch.size > self.batch.pagesize

class ProductView(BrowserView):
    """view of a product
    """

    template = ViewPageTemplateFile('templates/product.pt')

    def __call__(self):
        return self.template()
    
    @memoize
    def title(self):
        if IVariation.providedBy(self.context):
            return '%s (%s: %s)' % (self.product.Title().decode('utf-8'), self.context.getType().decode('utf-8'), self.context.Title().decode('utf-8'))
        return self.context.Title()
    
    @property
    @memoize
    def description(self):
        return self.context.Description() or self.product.Description()
    
    @property
    @memoize
    def text(self):
        return self.context.getText() or self.product.getText()
    
    @property
    @memoize
    def image(self):
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        width = int(props.getProperty('thumb_width_detail', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        context = None
        if self.context.getImage():
            context = self.context
        elif self.product.getImage():
            context = self.product
        if context is None:
            return None
        return {'caption': context.getImageCaption(),
                'thumb': '%s/%s' % (context.absolute_url(), width),
                'url': '%s/image_preview' % context.absolute_url()}
    
    @property
    @memoize
    def images(self):
        images = []
        odd = False
        i = 0
                      
        context = None
        
        if self.context.getImage():
            """ the variation have a image
            """
            image = self.image
            if image:
                image['parity'] = 'odd'            
                images.append(image)
                odd = True
                i = 1
            context = self.context
        elif not IImaging(self.context).getImages():
            """ the variation have not a image and not images in the content
            """
            image = self.image
            if image:
                image['parity'] = 'odd'            
                images.append(image)
                odd = True
                i = 1
            context = self.product
        else:
            """ the variation have not a image but a images in the content
            """
            context = self.context
                
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        width = int(props.getProperty('thumb_width_detail', 0))
        width = width and 'image/thumb?width=%s' % width or 'image_thumb'
        
        for image_raw in IImaging(context).getImages():
            image = {'url': '%s/image_preview' % (image_raw.getURL()),
                     'thumb': '%s/%s' % (image_raw.getURL(), width),
                     'caption': image_raw.Title
                    }
            odd = not odd
            if odd:
                image['parity'] = 'odd'
            else:
                image['parity'] = 'even'
            images.append(image)
            i += 1
          
        return images
          
    @property
    @memoize
    def product(self):
        context = aq_inner(self.context)
        if IVariation.providedBy(context):
            return aq_parent(context)
        return self.context
    
    @property
    @memoize
    def price(self):
        return CurrencyAware(IPricing(self.product).getPrice())
      
    @property
    @memoize
    def base_price(self):
        return CurrencyAware(IPricing(self.product).getBasePrice())
    
    @property
    @memoize
    def offer(self):
        return self.price.getValue() < self.base_price.getValue()
    
    @property
    @memoize
    def variations(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        results = catalog(object_provides=IVariation.__identifier__, path={'query': '/'.join(self.product.getPhysicalPath())})
        variations = {}
        for variation in results:
            if not variations.has_key(variation.getType):
                variations[variation.getType] = []
            if not variation.getAddPrice:
                price_adapter = IPricing(variation.getObject())
            variations[variation.getType].append({
                'uid': variation.UID,
                'name': variation.Title,
                'price': CurrencyAware(variation.getAddPrice and self.price.getValue() + float(variation.getPrice) or price_adapter.getPrice()),
                'base_price': CurrencyAware(variation.getAddPrice and self.base_price.getValue() + float(variation.getPrice) or price_adapter.getBasePrice())})
        return [{'name': type[0],
                 'variations': type[1]} for type in variations.items()]

class VariationsView(FolderContentsView):
    """management view of all variations
    """
    
    def contents_table(self):
        table = FolderContentsTable(self.context, self.request, {'object_provides': IVariation.__identifier__})
        return table.render()


class ImagesView(ProductView, FolderContentsTable):
    """management view of all images
    """
    implements(IFolderContentsView)

    template = ViewPageTemplateFile('templates/images.pt')
    
    def __call__(self):
        return self.template()
    
    @property
    @memoize
    def items(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        plone_view = getMultiAdapter((self.context, self.request), name=u'plone')
        utils = getToolByName(self.context, 'plone_utils')
        wftool = getToolByName(self.context, 'portal_workflow')
        results = catalog(object_provides=IImageContent.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()),
                                                                              'depth': 1})
        images = []
        odd = True
        for image in results:
            images.append({'uid': image.UID,
                           'id': image.getId,
                           'modified': plone_view.toLocalizedTime(image.ModificationDate, long_format=1),
                           'state_title': wftool.getTitleForStateOnType(image.review_state, image.portal_type),
                           'state_class': 'state-' + utils.normalizeString(image.review_state),
                           'is_expired': self.context.isExpired(image),
                           'title_or_id': image.pretty_title_or_id(),
                           'table_row_class': odd and 'odd' or 'even',
                           'path': image.getPath,
                           'relative_url': image.getURL(relative=True),
                           'image_thumb': '%s/image_thumb' % image.getURL(),
                           'url': {'edit': '%s/edit' % image.getURL(),
                           'sharing': '%s/@@sharing' % image.getURL()}})
            """Thumb with height width parameters... ??? """
            odd = not odd
        return images

class PricesView(ProductView, FolderContentsTable):
    """management view of all prices
    """
    implements(IFolderContentsView)

    template = ViewPageTemplateFile('templates/prices.pt')
    
    def __call__(self):
        if self.request.get('prices', None):
            prices = self.context.objectIds()
            for price in self.request.get('prices', []):
                if not isinstance(price, str) and price.id in prices:
                    self.context[price.id].setPrice(price.price)
                    self.context[price.id].reindexObject()
        return self.template()
    
    @property
    @memoize
    def items(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        plone_view = getMultiAdapter((self.context, self.request), name=u'plone')
        utils = getToolByName(self.context, 'plone_utils')
        wftool = getToolByName(self.context, 'portal_workflow')
        results = catalog(object_provides=IPrice.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath()), 'depth': 1})
        prices = []
        odd = True
        for price in results:
            prices.append({'uid': price.UID,
                           'id': price.getId,
                           'modified': plone_view.toLocalizedTime(price.ModificationDate, long_format=1),
                           'state_title': wftool.getTitleForStateOnType(price.review_state, price.portal_type),
                           'state_class': 'state-' + utils.normalizeString(price.review_state),
                           'is_expired': self.context.isExpired(price),
                           'title_or_id': price.pretty_title_or_id(),
                           'table_row_class': odd and 'odd' or 'even',
                           'raw_price': price.getPrice,
                           'price': CurrencyAware(price.getPrice),
                           'path': price.getPath,
                           'relative_url': price.getURL(relative=True),
                           'url': {'edit': '%s/edit' % price.getURL(),
                                   'sharing': '%s/@@sharing' % price.getURL()}})
            odd = not odd
        return prices

class VariationView(ProductView):
    """view of a variation
    """
    template = ViewPageTemplateFile('templates/variation.pt')

class PCommerceConfigletView(BrowserView):
    """PCommerce configlet
    """

    template = ViewPageTemplateFile('templates/configlet.pt')
    properties = ('productname','gtc',)
    values = {}

    def __call__(self):
        self.request.set('disable_border', True)
        self.errors = {}
        
        props = getToolByName(self.context, 'portal_properties').pcommerce_properties
        if self.request.form.has_key('pcommerce_save') and self.request.form.get('taxes', []):
            adapter = ITaxes(self.context)
            taxes = []
            raw = self.request.form.get('taxes', [])
            for tax in raw:
                if not tax.has_key('remove') or not tax['remove']:
                    try:
                        tax = {'id': tax['id'],
                               'tax': float(tax['tax']),
                               'zone': tax['zone']}
                        if tax['zone'] == '':
                            self.errors[tax['id']] = _(u'Please provide a zone name')
                        if not self.errors.has_key(tax['id']):
                            taxes.append(tax)
                    except:
                        self.errors[tax['id']] = _(u'Please enter a floating point number (e.g. 7.6)')
            for prop in self.properties:
                self.values[prop] = self.request.form.get(prop, None)
                if self.values[prop] == '':
                    self.values[prop] = None
                if self.values[prop] is None:
                    self.errors[prop] = _p(u'This field is required')
            
            if not self.errors:
                adapter.edit(taxes)
                IStatusMessage(self.request).addStatusMessage(_p('Properties saved'), 'info')
                for prop in self.properties:
                    if prop == 'columns':
                        self.values[prop] = int(self.values[prop])
                    props._setPropValue(prop, self.values[prop])
            else:
                IStatusMessage(self.request).addStatusMessage(_p(u'Please correct the indicated errors'), 'error')

        for prop in self.properties:
            self.values[prop] = props.getProperty(prop, '')
        
        return self.template()
    
    @property
    @memoize
    def taxes(self):
        utils = getToolByName(self.context, 'plone_utils')
        taxes = ITaxes(self.context)
        return [{'id': utils.normalizeString(zone),
                 'zone': zone,
                 'tax': tax} for zone, tax in taxes.items()]