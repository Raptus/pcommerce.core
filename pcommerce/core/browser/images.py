from zope.component import getMultiAdapter
from zope.interface import implements

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface.image import IImageContent

from plone.memoize.instance import memoize
from plone.app.content.browser.interfaces import IFolderContentsView
from plone.app.content.browser.foldercontents import FolderContentsTable

from pcommerce.core.browser.product import Product

class Images(Product, FolderContentsTable):
    """management view of all images
    """
    implements(IFolderContentsView)

    template = ViewPageTemplateFile('images.pt')
    
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
