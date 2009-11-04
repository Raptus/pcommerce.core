from zope.interface import implements
from pcommerce.core.interfaces import IAddress

class Address(object):
    """"""
    implements(IAddress)
    
    name = u''
    address1 = u''
    address2 = u''
    zip = u''
    city = u''
    country = u''
    zone = u''
    email = u''
    phone = u''
    
    def __init__(self,
                 name,
                 address1,
                 address2,
                 zip,
                 city,
                 country,
                 zone,
                 email,
                 phone):
        """"""
        self.name = name
        self.address1 = address1
        self.address2 = address2
        self.zip = zip
        self.city = city
        self.country = country
        self.zone = zone
        self.email = email
        self.phone = phone