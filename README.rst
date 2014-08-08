Introduction
============

PCommerce (Plone commerce) provides a simple shop system which supports:

* product variations
* multiple prices per product to support special prices per user or group
  (over the sharing tab) and prices only available for a specific time
  (by using the expiration date)
* multiple pluggable payment methods
* multiple pluggable shipment methods
* multiple taxes by zone
* pre and post tax charges per payment and shipment method
* component based checkout to easily customize the checkout process
* multiple currencies by using Products.CurrencyUtility


Installation
------------

Just add a pcommerce.core section to your buildout.cfg:

.. code-block:: bash

  [buildout]
  parts += pcommerce.core

There are some plugins like:

`pcommerce.payment.paypal
<https://pypi.python.org/pypi/pcommerce.payment.paypal/>`_

`pcommerce.payment.invoice
<https://pypi.python.org/pypi/pcommerce.payment.invoice>`_

Just check pypi for more.

Pluggable Payment Methods
-------------------------

A payment plugin consists of a named adapter implementing
pcommerce.core.interfaces.IPaymentMethod and named by the id (usually
the package name) of the method and one or more views injecting data
into the checkout process. The views are registered for the payment
method and have to implement pcommerce.core.interfaces.IPaymentView.
The name of the view corresponds to the name of the component where
the data has to be injected (e.g. payment, confirmation, overview etc.).

As an example of a simple payment plugin pcommerce.payment.invoice is
available, which simply collects a billing address and injects it into
the confirmation and order email.


Pluggable Shipment Methods
--------------------------

A shipment plugin works much like a payment plugin, the only differences
are the interfaces to be implemented by the adapter and the corresponding
views, which there are pcommerce.core.interfaces.IShipmentMethod respectively
pcommerce.core.interfaces.IShipmentView.

As an example pcommerce.shipment.parcel is available, which collects a delivery
address and injects it into the confirmation and order email.


Optional dependencies
---------------------

Products.CurrencyUtility - to add support for multiple currencies

ImageTag_CorePatch - to add support for dynamic image scaling
[http://www.zope.org/Members/bowerymarc/ImageTag_CorePatch/0.3/ImageTag_CorePatch.tgz]
