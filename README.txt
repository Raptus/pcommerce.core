Introduction
============

PCommerce (Plone commerce) provides a simple shop system which supports:

* product variations
* multiple prices per product to support special prices per user or group
  (over the sharing tab) and prices only available for a specific time
  (by using the expiration date)
* multiple pluggable payment methods
* multiple currencies by using Products.CurrencyUtility


Pluggable Payment Methods
-------------------------

To register a new payment method for PCommerce register a utility implementing
the IPaymentMethod interface. If your payment method requires data from the user
set the pre_view_name attribute of the utility to the name of the view implementing
IPreOrderView which provides the necessary fields. If you would like to display
information after ordering set the post_view_name attribute to the name of the
view providing those.

For a simple example pcommerce.email provides a payment method which simply sends
an email to the administrator containing the billing address.
