/*
 * PCommerce GetPrice
 */
(function($) {

  function pcommerceLoadPrice(){
    var variations = [];
    $('.buyViewlet select[name="cartVariation:list"]').each(function(i) {
      variations[i] = $(this).attr('value');
    });
    $('.portletInfoBox .priceInfo').load('getprice?v='+variations.join(','));
  }

  $('document').ready(function() {
    $('.buyViewlet select[name="cartVariation:list"]').each(function(i) {
      $(this).find('option').each(function(i) {
        html = $(this).html();
        $(this).html(html.substring(0, html.lastIndexOf('(')));
      });
    });

    if($('.buyViewlet select[name="cartVariation:list"]').length) {
      pcommerceLoadPrice();
    }
    $('.buyViewlet select[name="cartVariation:list"]').change(function(){
      pcommerceLoadPrice();
    });
  });

})(jQuery);
