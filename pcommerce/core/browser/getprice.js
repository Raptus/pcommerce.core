/*
 * PCommerce GetPrice
 */
jq('document').ready(function() {
    
    jq('.buyViewlet select[name=cartVariation:list]').each(function(i) {
        jq(this).find('option').each(function(i) {
            html = jq(this).html()
            jq(this).html(html.substring(0, html.lastIndexOf('(')))
        });
    });
    
    pcommerceLoadPrice();
    jq('.buyViewlet select[name=cartVariation:list]').change(function(){
        pcommerceLoadPrice();
    });
});

function pcommerceLoadPrice(){
    var variations = [];
    jq('.buyViewlet select[name=cartVariation:list]').each(function(i) {
        variations[i] = jq(this).attr('value');
    });
    
    jq('.portletInfoBox .priceInfo').load('getprice?v='+variations.join(','))
}