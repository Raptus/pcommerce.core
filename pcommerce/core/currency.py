from Products.CMFCore.utils import getToolByName
from zope.component import getSiteManager

try:
    from Products.CurrencyUtility.currency import CurrencyAware as CurrencyAwareBase
except:
    # CurrencyUtility not available

    import math


    class CurrencyAwareBase(object):
        """helper class to convert values between currencies"""

        value = 0
        context = None

        def __str__(self):
            return self.toString()

        def __init__(self, value, currency=None, rounding=None):
            self.value = float(value)
            if rounding is not None:
                self.rounding = rounding
            else:
                rounding = 0.05 # default value, round to 5 cents

        def getContext(self):
            """returns the context"""
            if self.context is None:
                self.context = getSiteManager()
            return self.context

        def getCurrencySymbol(self):
            """return the currency registered in site_properties"""
            props = getToolByName(self.getContext(), 'portal_properties').site_properties
            return props.getProperty('currency', '')

        def getValue(self, currency=None):
            """returns the value in the appropriate currency"""
            return self.value

        def getRoundedValue(self, currency=None):
            """returns the value in the appropriate currency rounded to 0.05"""
            value = self.getValue(currency)
            factor = 1.0 / self.rounding
            return float(int(math.ceil(value*factor)))/factor

        def toString(self, currency=None):
            """returns the value in the appropriate currency rounded to 0.05 including the symbol"""
            return "%s %0.2f" % (self.getCurrencySymbol(), self.getRoundedValue())

        def valueToString(self, currency=None):
            """returns the value in the appropriate currency rounded to 0.05"""
            return "%0.2f" % self.getRoundedValue()

        def safeToString(self, currency=None):
            """returns the value in the appropriate currency rounded to 0.05 including the currency-short-name"""
            return "%s %0.2f" % (self.getCurrencySymbol(), self.getRoundedValue())


class CurrencyAware(CurrencyAwareBase):
    """wrapper around CurrencyAware, so we can use proper rounding"""

    def __init__(self, value, currency=None):
        """
        retrieve the rounding from the properties, and
        call base init method
        """
        context = getSiteManager()
        props = getToolByName(context, 'portal_properties').pcommerce_properties
        rounding_cents = int(props.getProperty('rounding_cents', 5))
        rounding = rounding_cents * 0.01
        super(CurrencyAware, self).__init__(value, currency, rounding)
