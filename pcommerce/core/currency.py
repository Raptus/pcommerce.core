try:
    from Products.CurrencyUtility.currency import CurrencyAware
except:
    # CurrencyUtility not available

    import math
    
    from zope.interface import implements
    from zope.component import getSiteManager
    from Products.CMFCore.utils import getToolByName

    class CurrencyAware(object):
        """helper class to convert values between currencies"""
    
        value = 0
        context = None
    
        def __str__(self):
            return self.toString()
    
        def __init__(self, value, currency=None):
            self.value = float(value)
    
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
            return float(int(math.ceil(self.value*20)))/20
    
        def toString(self, currency=None):
            """returns the value in the appropriate currency rounded to 0.05 including the symbol"""
            return "%s %0.2f" % (self.getCurrencySymbol(), self.getRoundedValue())
        
        def valueToString(self, currency=None):
            """returns the value in the appropriate currency rounded to 0.05"""
            return "%0.2f" % self.getRoundedValue()
        
        def safeToString(self, currency=None):
            """returns the value in the appropriate currency rounded to 0.05 including the currency-short-name"""
            return "%s %0.2f" % (self.getCurrencySymbol(), self.getRoundedValue())
