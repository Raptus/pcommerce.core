"""Main product initializer
"""

from pcommerce.core.config import PROJECTNAME, permissions

from Products.Archetypes import atapi
from Products.CMFCore import utils as cmfutils
from Products.CMFCore.utils import getToolByName

from zope.i18nmessageid import MessageFactory
PCommerceMessageFactory = MessageFactory('pcommerce')

def initialize(context):

    from content import product, variation, price

    content_types, constructors, ftis = atapi.process_types(
        atapi.listTypes(PROJECTNAME),
        PROJECTNAME)

    for atype, constructor in zip(content_types, constructors):
        cmfutils.ContentInit("%s: %s" % (PROJECTNAME, atype.portal_type),
            content_types      = (atype,),
            permission         = permissions[atype.portal_type],
            extra_constructors = (constructor,),
            ).initialize(context)