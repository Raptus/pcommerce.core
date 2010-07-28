from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from pcommerce.core.browser.product import Product

class Variation(Product):
    """view of a variation
    """
    template = ViewPageTemplateFile('variation.pt')
