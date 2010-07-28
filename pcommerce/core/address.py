import re
from persistent import Persistent

from zope.i18n import translate
from zope.interface import implements, Interface
from zope.component import adapts

from Products.CMFPlone import PloneMessageFactory as _p
from Products.validation.validators.BaseValidators import EMAIL_RE
email_re = re.compile(EMAIL_RE)

from pcommerce.core.interfaces import IAddress, IAddressFactory
from pcommerce.core import PCommerceMessageFactory as _

class Address(Persistent):
    """"""
    implements(IAddress)
    
    salutation = u''
    firstname = u''
    lastname = u''
    company = u''
    address1 = u''
    address2 = u''
    zip = u''
    city = u''
    country = u''
    zone = u''
    email = u''
    phone = u''
    
    def __init__(self,
                 salutation,
                 firstname,
                 lastname,
                 company,
                 address1,
                 address2,
                 zip,
                 city,
                 country,
                 zone,
                 email,
                 phone):
        """"""
        self.salutation = salutation
        self.firstname = firstname
        self.lastname = lastname
        self.company = company
        self.address1 = address1
        self.address2 = address2
        self.zip = zip
        self.city = city
        self.country = country
        self.zone = zone
        self.email = email
        self.phone = phone
    
    def mailInfo(self, request, lang=None, customer=False):
        address = [(self.salutation and translate(_((self.salutation == 'mr' and 'Mr.' or 'Mrs. / Ms.')), context=request, target_language=lang) +' ' or '') + self.firstname +' '+ self.lastname,
                   self.company, 
                   self.address1, 
                   self.address2, 
                   self.zip + (self.zip is not None and ' ') + self.city, 
                   self.country, 
                   self.zone]
        address = [value for value in address if value]
        address.append('')
        address.append(self.email)
        if self.phone:
            address.append(self.phone)
        return '\n'.join(address)

class AddressFactory(object):
    adapts(Interface)
    implements(IAddressFactory)
    
    required = ('firstname', 'lastname', 'address1', 'city', 'country', 'phone')
    
    def __init__(self, request):
        self.request = request
        
    def validate(self, tag):
        errors = {}
        required = self.required
        data = self.request.get(tag, {})
        for field in required:
            if not data.get(field, None):
                errors[tag+'.'+field] = _p(u'This field is required, please provide some information.')
            
        if not email_re.match(data.get('email', '')):
                errors[tag+'.'+'email'] = _p(u'Please submit a valid email address.')
        return errors
    
    def create(self, tag):
        data = self.request.get(tag, {})
        return Address(salutation = data.get('salutation', '').decode('utf-8'),
                       firstname  = data.get('firstname', '').decode('utf-8'),
                       lastname   = data.get('lastname', '').decode('utf-8'),
                       company    = data.get('company', '').decode('utf-8'),
                       address1   = data.get('address1', '').decode('utf-8'),
                       address2   = data.get('address2', '').decode('utf-8'),
                       zip        = data.get('zip', '').decode('utf-8'),
                       city       = data.get('city', '').decode('utf-8'),
                       country    = data.get('country', '').decode('utf-8'),
                       zone       = data.get('zone', '').decode('utf-8'),
                       email      = data.get('email', '').decode('utf-8'),
                       phone      = data.get('phone', '').decode('utf-8'),)
